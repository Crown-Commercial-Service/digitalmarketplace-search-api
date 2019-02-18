from app.main.services import search_service
from flask import json
import pytest

from app import create_app
from ..helpers import setup_authorization, make_standard_service


# Helpers for 'result_fields_check'

def odd(result_field):
    "Should be odd."
    return int(result_field) % 2 == 1


def even(result_field):
    "Should be even."
    return int(result_field) % 2 == 0


@pytest.mark.parametrize('query, expected_result_count, match_fields', (
    ('', 120, {}),
    ('filter_lot=SaaS', 30, {'lot': "SaaS".__eq__}),
    ('filter_serviceTypes=Implementation', 48, {'serviceTypes': lambda i: 'Implementation' in i}),
    ('filter_minimumContractPeriod=Hour', 40, {}),
    ('filter_phoneSupport=True', 60, {'id': odd}),
))
def test_single_filter_queries(query, expected_result_count, match_fields):
    check_query(query, expected_result_count, match_fields)


def test_basic_aggregations():
    check_aggregations_query(
        '',
        120,
        {'PaaS': (30).__eq__, 'SaaS': (30).__eq__, 'IaaS': (30).__eq__, 'SCS': (30).__eq__}
    )
    check_aggregations_query('filter_lot=SaaS', 30, {'SaaS': (30).__eq__})
    check_aggregations_query(
        'filter_minimumContractPeriod=Hour,Day',
        80,
        {'PaaS': (20).__eq__, 'SaaS': (20).__eq__, 'IaaS': (20).__eq__, 'SCS': (20).__eq__}
    )
    check_aggregations_query('filter_lot=SaaS&filter_minimumContractPeriod=Hour,Day', 20, {'SaaS': (20).__eq__})


def test_or_filters():
    check_query('filter_lot=SaaS,PaaS', 60, {'lot': ['SaaS', 'PaaS'].__contains__})
    check_query('filter_minimumContractPeriod=Hour,Day', 80, {})
    check_query('filter_datacentreTier=tia-942 tier 1,tia-942 tier 2', 120, {})
    check_query('filter_datacentreTier=tia-942 tier 3,tia-942 tier 2', 0, {})
    check_query('filter_minimumContractPeriod=Hour,Day&filter_datacentreTier=tia-942 tier 3,tia-942 tier 2', 0, {})


def test_and_filters():
    check_query(
        'filter_serviceTypes=Planning&filter_serviceTypes=Testing',
        24, {'serviceTypes': ['Planning', 'Testing'].__eq__}
    )

    check_query(
        'filter_serviceTypes=Planning&filter_serviceTypes=Implementation',
        0, {}
    )

    check_query('filter_lot=SaaS&filter_lot=PaaS', 0, {})


def test_filter_combinations():
    check_query(
        'filter_minimumContractPeriod=Hour&filter_phoneSupport=false',
        20, {'id': even}
    )

    check_query(
        'filter_minimumContractPeriod=Hour,Day&filter_phoneSupport=false',
        40, {'id': even}
    )

    check_query(
        'filter_minimumContractPeriod=Hour,Day&filter_phoneSupport=false&filter_lot=SaaS',
        20, {'id': even}
    )

    check_query(
        'filter_minimumContractPeriod=Hour&filter_lot=SaaS',
        10, {'lot': 'SaaS'.__eq__}
    )

    check_query(
        'q=12&filter_minimumContractPeriod=Hour&filter_lot=SaaS',
        1, {'lot': 'SaaS'.__eq__, 'id': '12'.__eq__}
    )

    check_query(
        'q=12&filter_minimumContractPeriod=Hour&filter_lot=PaaS', 0, {}
    )


def test_special_characters():
    # Elasticserch reserved characters:
    #   + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /

    check_query('q=Service%3D1', 1, {})  # =
    check_query('q=Service%211', 1, {})  # !
    check_query('q=Service%5E1', 1, {})  # ^
    check_query('q=Service%7E1', 1, {})  # ~
    check_query('q=Service%3F1', 1, {})  # ?
    check_query('q=Service%3A1', 1, {})  # :
    check_query('q=Service%5C 1', 1, {})  # \
    check_query('q=Service%2F1', 1, {})  # /
    check_query('q=Service%26%261', 1, {})  # &&
    check_query('q=Service 1*', 1, {})

    check_query('q=Service>1', 1, {})
    check_query('q=Service<1', 1, {})

    check_query('q=Service(1', 1, {})
    check_query('q=Service)1', 1, {})

    check_query('q=Service{1', 1, {})
    check_query('q=Service}1', 1, {})

    check_query('q=Service[1', 1, {})
    check_query('q=Service]1', 1, {})

    check_query('q=id%3A1', 0, {})


def test_basic_keyword_search():
    check_query('q=Service', 120, {})


def test_and_keyword_search():
    check_query('q=Service 1', 1, {})

    check_query('q=Service 1 2 3', 0, {})

    check_query('q=+Service +1', 1, {})
    check_query('q=Service %26100', 1, {})
    check_query('q=Service %26 100', 0, {})
    check_query('q=Service %26%26100', 1, {})
    check_query('q=Service %26%26 100', 0, {})


def test_phrase_keyword_search():
    check_query('q="Service 12"', 1, {})

    check_query('q="Service -12"', 1, {})
    check_query('q=Service -12"', 119, {})
    check_query('q="Service -12', 119, {})

    check_query('q="Service | -12"', 1, {})
    check_query('q="Service %26 12"', 1, {})


def test_negated_keyword_search():
    check_query('q=Service -12', 119, {})

    check_query('q=12 -12', 0, {})


def test_or_keyword_search():
    check_query('q=Service || 12', 120, {})

    check_query('q=missing | 12', 1, {})
    check_query('q=missing || 12', 1, {})


def test_escaped_characters():
    check_query(r'q=\"Service | 12\"', 120, {})
    check_query(r'q=\-12', 1, {})
    check_query(r'q=Service \|12', 1, {})
    check_query(r'q=Service \| 12', 0, {})


@pytest.fixture(scope='module', autouse=True)
def dummy_services(services_mapping_definition):
    """Fixture that indexes a bunch of fake G-Cloud services so that searching can be tested."""

    app = create_app('test')
    test_client = app.test_client()

    setup_authorization(app)
    with app.app_context():
        response = test_client.put(
            '/index-to-create',
            data=json.dumps({"type": "index", "mapping": "services", }),
            content_type="application/json",
        )
        assert response.status_code in (200, 201)
        services = list(create_services(120))
        for service in services:
            test_client.put(
                '/index-to-create/services/%s' % service["document"]["id"],
                data=json.dumps(service), content_type='application/json'
            )
            search_service.refresh('index-to-create')
    yield
    test_client.delete('/index-to-create')


# '/search' request helpers

def create_services(number_of_services):
    for i in range(number_of_services):
        yield make_standard_service(
            id=str(i),
            serviceName="Service {}".format(i),
            phoneSupport=bool(i % 2),
            minimumContractPeriod=["Hour", "Day", "Month"][i % 3],
            lot=["SaaS", "PaaS", "IaaS", "SCS"][i % 4],
            serviceTypes=[
                "Implementation",
                "Ongoing support",
                "Planning",
                "Testing",
                "Training",
                "Implementation",  # repeated to always get 2 element slice
            ][i % 5:(i % 5) + 2],
        )


def search_results(query):
    app = create_app('test')
    test_client = app.test_client()
    setup_authorization(app)

    response = test_client.get('/index-to-create/services/search?%s' % query)
    return json.loads(response.get_data())


def aggregations_results(query):
    app = create_app('test')
    test_client = app.test_client()
    setup_authorization(app)

    response = test_client.get('/index-to-create/services/aggregations?{}&aggregations=lot'.format(query))
    return json.loads(response.get_data())


# Result checker functions

def count_for_query(query, expected_count):
    assert query['meta']['total'] == expected_count, (
        "Unexpected number of results. Expected {}, received {}:\n{}".format(
            expected_count,
            query['meta']['total'],
            json.dumps(query, indent=2)
        )
    )


def result_fields_check(query, check_fns):
    services = query['documents']
    for field in check_fns:
        assert all(check_fns[field](service[field]) for service in services), (
            "Field '{}' check '{}' failed for search results:\n{}".format(
                field, check_fns[field].__doc__,
                json.dumps(query, indent=2)
            )
        )


def aggregation_fields_check(query, check_fns):
    aggregations = query['aggregations']
    for field in check_fns:
        assert all(check_fns[field](aggregations[agg][field]) for agg in aggregations), (
            "Field '{}' check '{}' failed for aggregation results:\n{}".format(
                field, check_fns[field].__doc__,
                json.dumps(query, indent=2)
            )
        )


def check_query(query, expected_result_count, match_fields):
    results = search_results(query)
    count_for_query(results, expected_result_count)
    result_fields_check(results, match_fields)


def check_aggregations_query(query, expected_result_count, match_fields):
    results = aggregations_results(query)
    count_for_query(results, expected_result_count)

    aggregation_fields_check(results, match_fields)
