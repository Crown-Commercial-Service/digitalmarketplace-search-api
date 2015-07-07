from app.main.services.process_request_json import \
    convert_request_json_into_index_json
from nose.tools import assert_equal


def test_should_add_filter_fields_to_index_json():
    request = {
        "lot": "SaaS",
        "freeOption": True,
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
        "filter_freeOption": True,
    })


def test_should_make__match_array_fields():
    request = {
        "lot": "SaaS",
        "serviceTypes": ["One", "Two", "Three"],
        "networksConnected": ["Internet", "PSN"],
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
        "serviceTypes": ["One", "Two", "Three"],
        "filter_serviceTypes": ["one", "two", "three"],
        "filter_networksConnected": ["internet", "psn"],
    })


def test_should_ignore_non_filter_and_non_text_fields():
    request = {
        "lot": "SaaS",
        "ignore": "Unchanged",
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
    })


def test_should_remove_raw_filter_fields_that_are_non_text():
    request = {
        "lot": "SaaS",
        "freeOption": False,
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result["lot"], "SaaS")
    assert_equal(result["filter_lot"], "saas")
    assert_equal(result["filter_freeOption"], False)
    assert_equal("freeOption" in result, False)
