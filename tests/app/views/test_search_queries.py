from app.main.services import search_service
from flask import json
from nose.tools import assert_equal, ok_
import pytest

from app import create_app
from ..helpers import setup_authorization
from ..helpers import default_service

import tests.conftest
import contextlib


pytestmark = pytest.mark.usefixtures("services_mapping")


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
    ('filter_openSource=true', 60, {'id': odd}),
))
def test_single_filter_queries(query, expected_result_count, match_fields):
    check_query(query, expected_result_count, match_fields)


def test_basic_aggregations():
    yield check_aggregations_query, '', 120, {'PaaS': (30).__eq__, 'SaaS': (30).__eq__, 'IaaS': (30).__eq__,
                                              'SCS': (30).__eq__}
    yield check_aggregations_query, 'filter_lot=SaaS', 30, {'SaaS': (30).__eq__}
    yield check_aggregations_query, 'filter_minimumContractPeriod=Hour,Day', 80, {'PaaS': (20).__eq__,
                                                                                  'SaaS': (20).__eq__,
                                                                                  'IaaS': (20).__eq__,
                                                                                  'SCS': (20).__eq__}
    yield check_aggregations_query, 'filter_lot=SaaS&filter_minimumContractPeriod=Hour,Day', 20, {'SaaS': (20).__eq__}


def test_or_filters():
    yield (check_query, 'filter_lot=SaaS,PaaS',
           60, {'lot': ['SaaS', 'PaaS'].__contains__})
    yield check_query, 'filter_minimumContractPeriod=Hour,Day', 80, {}
    yield (check_query, 'filter_datacentreTier=tia-942 tier 1,tia-942 tier 2',
           120, {})
    yield (check_query, 'filter_datacentreTier=tia-942 tier 3,tia-942 tier 2',
           0, {})
    yield (check_query,
           'filter_minimumContractPeriod=Hour,Day&filter_datacentreTier=tia-942 tier 3,tia-942 tier 2',
           0, {})


def test_and_filters():
    yield (check_query,
           'filter_serviceTypes=Planning&filter_serviceTypes=Testing',
           24, {'serviceTypes': ['Planning', 'Testing'].__eq__})

    yield (check_query,
           'filter_serviceTypes=Planning&filter_serviceTypes=Implementation',
           0, {})

    yield check_query, 'filter_lot=SaaS&filter_lot=PaaS', 0, {}


def test_filter_combinations():
    yield (check_query,
           'filter_minimumContractPeriod=Hour&filter_openSource=false',
           20, {'id': even})

    yield (check_query,
           'filter_minimumContractPeriod=Hour,Day&filter_openSource=false',
           40, {'id': even})

    yield (check_query,
           'filter_minimumContractPeriod=Hour,Day&filter_openSource=false&filter_lot=SaaS',
           20, {'id': even})

    yield (check_query,
           'filter_minimumContractPeriod=Hour&filter_lot=SaaS',
           10, {'lot': 'SaaS'.__eq__})

    yield (check_query,
           'q=12&filter_minimumContractPeriod=Hour&filter_lot=SaaS',
           1, {'lot': 'SaaS'.__eq__, 'id': '12'.__eq__})

    yield (check_query,
           'q=12&filter_minimumContractPeriod=Hour&filter_lot=PaaS', 0, {})


def test_special_characters():
    # Elasticserch reserved characters:
    #   + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /

    yield (check_query, 'q=Service%3D1', 1, {})  # =
    yield (check_query, 'q=Service%211', 1, {})  # !
    yield (check_query, 'q=Service%5E1', 1, {})  # ^
    yield (check_query, 'q=Service%7E1', 1, {})  # ~
    yield (check_query, 'q=Service%3F1', 1, {})  # ?
    yield (check_query, 'q=Service%3A1', 1, {})  # :
    yield (check_query, 'q=Service%5C 1', 1, {})  # \
    yield (check_query, 'q=Service%2F1', 1, {})  # /
    yield (check_query, 'q=Service%26%261', 1, {})  # &&
    yield (check_query, 'q=Service 1*', 1, {})

    yield (check_query, 'q=Service>1', 1, {})
    yield (check_query, 'q=Service<1', 1, {})

    yield (check_query, 'q=Service(1', 1, {})
    yield (check_query, 'q=Service)1', 1, {})

    yield (check_query, 'q=Service{1', 1, {})
    yield (check_query, 'q=Service}1', 1, {})

    yield (check_query, 'q=Service[1', 1, {})
    yield (check_query, 'q=Service]1', 1, {})

    yield (check_query, 'q=id%3A1', 0, {})


def test_basic_keyword_search():
    yield (check_query,
           'q=Service',
           120, {})


def test_and_keyword_search():
    yield (check_query,
           'q=Service 1',
           1, {})

    yield (check_query, 'q=Service 1 2 3', 0, {})

    yield (check_query, 'q=+Service +1', 1, {})
    yield (check_query, 'q=Service %26100', 1, {})
    yield (check_query, 'q=Service %26 100', 0, {})
    yield (check_query, 'q=Service %26%26100', 1, {})
    yield (check_query, 'q=Service %26%26 100', 0, {})


def test_phrase_keyword_search():
    yield (check_query, 'q="Service 12"', 1, {})

    yield (check_query, 'q="Service -12"', 1, {})
    yield (check_query, 'q=Service -12"', 119, {})
    yield (check_query, 'q="Service -12', 119, {})

    yield (check_query, 'q="Service | -12"', 1, {})
    yield (check_query, 'q="Service %26 12"', 1, {})


def test_negated_keyword_search():
    yield (check_query,
           'q=Service -12',
           119, {})

    yield (check_query, 'q=12 -12', 0, {})


def test_or_keyword_search():
    yield (check_query,
           'q=Service || 12',
           120, {})

    yield (check_query, 'q=missing | 12', 1, {})
    yield (check_query, 'q=missing || 12', 1, {})


def test_escaped_characters():
    yield (check_query, 'q=\\"Service | 12\\"', 120, {})
    yield (check_query, 'q=\-12', 1, {})
    yield (check_query, 'q=Service \|12', 1, {})
    yield (check_query, 'q=Service \| 12', 0, {})


@pytest.fixture(scope='module', autouse=True)
def dummy_services():
    """Fixture that indexes a bunch of fake G-Cloud services so that searching can be tested."""

    # Create a context where get_services_mapping has been patched, despite that fixture being function-
    # scoped - see commentary below.
    with contextlib.contextmanager(tests.conftest.services_mapping)():
        app = create_app('test')
        test_client = app.test_client()

        setup_authorization(app)

        with app.app_context():
            test_client.put(
                '/index-to-create',
                data=json.dumps({"type": "index"}),
                content_type="application/json",
            )
            services = list(create_services(120))
            for service in services:
                test_client.put(
                    '/index-to-create/services/%s' % service["service"]["id"],
                    data=json.dumps(service), content_type='application/json'
                )
                search_service.refresh('index-to-create')
        # `yield` is within the services_mapping contextmanager (created above).
        # This has the effect of making the services_mapping fixture module-scoped, for this module only.
        # This is safe, because none of the tests here actually modify the mapping. It is necessary,
        # because many of the tests use the (deprecated) nosetests `yield` format. These do not support
        # function-scoped fixtures, and would therefore fail to use the services_mapping fixture, despite
        # the pytestmark at the top of this file.
        # Once all of the yield-style tests have been converted to use pytest.mark.parametrize, then the
        # line below can move back outside the services_mapping contextmanager.
        yield
    test_client.delete('/index-to-create')


# '/search' request helpers

def create_services(number_of_services):
    for i in range(number_of_services):
        yield default_service(
            id=str(i),
            serviceName="Service {}".format(i),
            openSource=bool(i % 2),
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
    assert_equal(
        query['meta']['total'], expected_count,
        "Unexpected number of results. Expected {}, received {}:\n{}".format(
            expected_count, query['meta']['total'],
            json.dumps(query, indent=2)
        )
    )


def result_fields_check(query, check_fns):
    services = query['services']
    for field in check_fns:
        ok_(all(check_fns[field](service[field]) for service in services),
            "Field '{}' check '{}' failed for search results:\n{}".format(
                field, check_fns[field].__doc__,
                json.dumps(query, indent=2)))


def aggregation_fields_check(query, check_fns):
    aggregations = query['aggregations']
    for field in check_fns:
        ok_(all(check_fns[field](aggregations[agg][field]) for agg in aggregations),
            "Field '{}' check '{}' failed for aggregation results:\n{}".format(
                field, check_fns[field].__doc__,
                json.dumps(query, indent=2)))


def check_query(query, expected_result_count, match_fields):
    results = search_results(query)
    count_for_query(results, expected_result_count)
    result_fields_check(results, match_fields)


def check_aggregations_query(query, expected_result_count, match_fields):
    results = aggregations_results(query)
    count_for_query(results, expected_result_count)

    aggregation_fields_check(results, match_fields)
