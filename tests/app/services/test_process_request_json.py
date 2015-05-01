from app.main.services.process_request_json import \
    convert_request_json_into_index_json
from nose.tools import assert_equal


def test_should_make_filter_match_string_fields():
    request = {
        "lot": "SaaS"
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result["lot"], "SaaS")
    assert_equal(result["filter_lot"], "saas")


def test_should_make__match_array_fields():
    request = {
        "lot": "SaaS",
        "serviceTypes": ["One", "Two", "Three"]
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result["lot"], "SaaS")
    assert_equal(result["filter_lot"], "saas")
    assert_equal(result["serviceTypes"], ["One", "Two", "Three"])
    assert_equal(result["filter_serviceTypes"], ["one", "two", "three"])


def test_should_ignore_non_filter_fields():
    request = {
        "lot": "SaaS",
        "ignore": "Unchanged",
    }

    result = convert_request_json_into_index_json(request)
    assert_equal(result["lot"], "SaaS")
    assert_equal(result["filter_lot"], "saas")
    assert_equal(result["ignore"], "Unchanged")
    assert_equal("filter_ignore" in result, False)


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