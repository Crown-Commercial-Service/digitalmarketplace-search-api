import pytest

from app.main.services.process_request_json import \
    convert_request_json_into_index_json
from nose.tools import assert_equal


pytestmark = pytest.mark.usefixtures("services_mapping")


def test_should_add_filter_fields_to_index_json(services_mapping):
    request = {
        "lot": "SaaS",
        "phoneSupport": True,
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "dmagg_lot": "SaaS",
        "dmtext_lot": "SaaS",
        "dmfilter_lot": "SaaS",
        "dmfilter_phoneSupport": True,
    })


def test_should_make__match_array_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "serviceTypes": ["One", "Two", "Three"],
        "networksConnected": ["Internet", "PSN"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "dmagg_lot": "SaaS",
        "dmtext_lot": "SaaS",
        "dmfilter_lot": "SaaS",
        "dmtext_serviceTypes": ["One", "Two", "Three"],
        "dmfilter_serviceTypes": ["One", "Two", "Three"],
        "dmfilter_networksConnected": ["Internet", "PSN"],
    })


def test_should_ignore_non_filter_and_non_text_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "ignore": "Unchanged",
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert_equal(result, {
        "dmagg_lot": "SaaS",
        "dmtext_lot": "SaaS",
        "dmfilter_lot": "SaaS",
    })


def test_should_add_parent_category(services_mapping):
    request = {
        "serviceCategories": ["Accounts payable"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result["dmtext_serviceCategories"] == [
        "Accounts payable",
        "Accounting and finance",
    ]

    assert result["dmfilter_serviceCategories"] == [
        "Accounts payable",
        "Accounting and finance",
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

    assert result["dmtext_serviceCategories"] == [
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

    assert result["dmtext_serviceCategories"] == [
        "Crops", "Animals", "Agriculture", "Agriculture",
    ]


def test_missing_field_in_transformation(services_mapping):
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "supplierName",
                "any_of": [
                    "foo",
                ],
                "append_value": [
                    "bar"
                ]
            }
        },
    ]
    request = {
        "serviceFeatures": ["wibble"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    # really just checking this case doesn't throw!

    assert result == {
        "dmtext_serviceFeatures": ["wibble"],
    }


def test_create_new_field_in_transformation(services_mapping):
    services_mapping.transform_fields = [
        {
            "append_conditionally": {
                "field": "supplierName",
                "any_of": [
                    "foo",
                ],
                "target_field": "serviceTypes",
                "append_value": [
                    "bar"
                ]
            }
        }
    ]
    request = {
        "supplierName": ["foo"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result == {
        "dmtext_supplierName": ["foo"],
        "dmtext_serviceTypes": ["bar"],
        "dmfilter_serviceTypes": ["bar"],
    }


def test_service_id_hash_added_if_id_present(services_mapping):
    request = {
        "id": "999999999",
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result == {
        "dmtext_id": "999999999",
        "dmsortonly_serviceIdHash": "bb421fa35db885ce507b0ef5c3f23cb09c62eb378fae3641c165bdf4c0272949",
    }
