from app.main.services import search_service
from flask import json
from nose.tools import assert_equal, ok_

from app import create_app
from ..helpers import setup_authorization, teardown_authorization
from ..helpers import default_service


def test_single_filter_queries():
    yield check_query, '', 120, {}
    yield check_query, 'filter_lot=SaaS', 30, {'lot': matches("SaaS")}
    yield (check_query, 'filter_serviceTypes=Implementation',
           48, {'serviceTypes': contains('Implementation')})
    yield check_query, 'filter_minimumContractPeriod=Hour', 40, {}
    yield check_query, 'filter_openSource=true', 60, {'id': odd}


def test_or_filters():
    yield (check_query, 'filter_lot=SaaS,PaaS',
           60, {'lot': one_of(['SaaS', 'PaaS'])})
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
           24, {'serviceTypes': matches(['Planning', 'Testing'])})

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
           10, {'lot': matches('SaaS')})

    yield (check_query,
           'q=12&filter_minimumContractPeriod=Hour&filter_lot=SaaS',
           1, {'lot': matches('SaaS'), 'id': matches('12')})

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
    yield (check_query, 'q=Service %26 100', 1, {})
    yield (check_query, 'q=Service %26%26 100', 1, {})


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
    yield (check_query, 'q=Service \| 12', 1, {})


# Module setup and teardown
def setup_module():
    app = create_app('test')
    test_client = app.test_client()

    setup_authorization(app)

    with app.app_context():
        services = list(create_services(120))
        for service in services:
            test_client.put(
                '/index-to-create/services/%s' % service["service"]["id"],
                data=json.dumps(service), content_type='application/json'
            )
            search_service.refresh('index-to-create')


def teardown_module():
    app = create_app('test')
    test_client = app.test_client()

    test_client.delete('/index-to-create')
    teardown_authorization()


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


def search_or_results(query_or_results):
    if isinstance(query_or_results, dict):
        return query_or_results
    else:
        return search_results(query_or_results)


# Result checker functions

def count_for_query(query, expected_count):
    results = search_or_results(query)
    assert_equal(
        results['meta']['total'], expected_count,
        "Unexpected number of results. Expected {}, received {}:\n{}".format(
            expected_count, results['meta']['total'],
            json.dumps(results, indent=2)
        )
    )

    return results


def result_fields_check(query, check_fns):
    results = search_or_results(query)
    services = results['services']
    for field in check_fns:
        ok_(all(check_fns[field](service[field]) for service in services),
            "Field '{}' check '{}' failed for search results:\n{}".format(
                field, check_fns[field].__doc__,
                json.dumps(results, indent=2)))

    return results


def check_query(query, expected_result_count, match_fields):
    results = search_or_results(query)
    count_for_query(results, expected_result_count)
    result_fields_check(results, match_fields)


# Helpers for 'result_fields_check'

def matches(expected_field):
    check = lambda result_field: result_field == expected_field
    check.__doc__ = "Should match '%s'" % expected_field
    check.__name__ = "matches %s" % expected_field

    return check


def contains(expected_field):
    check = lambda result_field: expected_field in result_field
    check.__doc__ = "Should contain '%s'" % expected_field
    check.__name__ = "contains %s" % expected_field

    return check


def one_of(expected_fields):
    check = lambda result_field: result_field in expected_fields
    check.__doc__ = "Should be in %s" % expected_fields
    check.__name__ = "one_of %s" % expected_fields

    return check


def odd(result_field):
    "Should be odd."
    return int(result_field) % 2 == 1


def even(result_field):
    "Should be event."
    return int(result_field) % 2 == 0
