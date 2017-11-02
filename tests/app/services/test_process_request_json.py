import pytest

import app.mapping
from app.main.services.process_request_json import \
    convert_request_json_into_index_json
from nose.tools import assert_equal


pytestmark = pytest.mark.usefixtures("services_mapping")


def test_should_add_filter_fields_to_index_json(services_mapping):
    request = {
        "lot": "SaaS",
        "freeOption": True,
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
        "filter_freeOption": True,
    })


def test_should_make__match_array_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "serviceTypes": ["One", "Two", "Three"],
        "networksConnected": ["Internet", "PSN"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
        "serviceTypes": ["One", "Two", "Three"],
        "filter_serviceTypes": ["one", "two", "three"],
        "filter_networksConnected": ["internet", "psn"],
    })


def test_should_ignore_non_filter_and_non_text_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "ignore": "Unchanged",
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "lot": "SaaS",
        "filter_lot": "saas",
    })


def test_should_remove_raw_filter_fields_that_are_non_text(services_mapping):
    request = {
        "lot": "SaaS",
        "freeOption": False,
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result["lot"], "SaaS")
    assert_equal(result["filter_lot"], "saas")
    assert_equal(result["filter_freeOption"], False)
    assert_equal("freeOption" in result, False)


def test_should_add_parent_category(services_mapping):
    request = {
        "serviceCategories": ["Accounts payable"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["serviceCategories"] == [
        "Accounts payable",
        "Accounting and finance",
    ]

    assert result["filter_serviceCategories"] == [
        "accountspayable",
        "accountingandfinance",
    ]


def test_append_conditionally_does_not_duplicate_values(services_mapping):
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "serviceCategories",
                "any_of": [
                    "Crops",
                    "Animals",
                ],
                "append_value": [
                    "Agriculture",
                ]
            }
        }
    ]

    request = {
        "serviceCategories": ["Crops", "Animals"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["serviceCategories"] == [
        "Crops", "Animals", "Agriculture",
    ]  # not ["Crops", "Animals", "Agriculture", "Agriculture"]


def test_duplicative_transformations_do_duplicate_values(services_mapping):
    # Transformations generated from the frameworks script DO NOT attempt to generate duplicate
    # values in the way that this test does, but in principle some set of transformations might.
    # We might decide in future that we want to change the append_conditionally implementation
    # to remove this duplication, but its current behaviour (i.e. ignoring whether values
    # are already in the destination field) seems consistent with the documented behaviour
    # of Elasticsearch's "Append" processor
    # <https://www.elastic.co/guide/en/elasticsearch/reference/current/append-processor.html>.
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "serviceCategories",
                "any_of": [
                    "Crops",
                ],
                "append_value": [
                    "Agriculture"
                ]
            }
        },
        {
            "append_conditionally": {
                "field": "serviceCategories",
                "any_of": [
                    "Animals",
                ],
                "append_value": [
                    "Agriculture"
                ]
            }
        },
    ]

    request = {
        "serviceCategories": ["Crops", "Animals"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["serviceCategories"] == [
        "Crops", "Animals", "Agriculture", "Agriculture",
    ]


def test_missing_field_in_transformation(services_mapping):
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "someField",
                "any_of": [
                    "foo",
                ],
                "append_value": [
                    "bar"
                ]
            }
        },
    ]
    services_mapping.text_fields_set = {'someField', 'otherField'}
    request = {
        "otherField": ["wibble"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    # really just checking this case doesn't throw!

    assert result == {
        "otherField": ["wibble"],
    }


def test_create_new_field_in_transformation(services_mapping):
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "someField",
                "any_of": [
                    "foo",
                ],
                "target_field": "newField",
                "append_value": [
                    "bar"
                ]
            }
        }
    ]
    services_mapping.text_fields_set = {'someField', 'newField'}
    request = {
        "someField": ["foo"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["newField"] == [
        "bar",
    ]

    assert result["someField"] == ["foo"]


def test_service_id_hash_added_if_id_present(services_mapping):
    request = {
        "id": "999999999",
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["id"] == "999999999"

    assert app.mapping.SERVICE_ID_HASH_FIELD_NAME in result
