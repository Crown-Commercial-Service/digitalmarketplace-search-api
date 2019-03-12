import pytest

from app.main.services.process_request_json import \
    convert_request_json_into_index_json


pytestmark = pytest.mark.usefixtures("services_mapping")


def test_should_add_filter_fields_to_index_json(services_mapping):
    request = {
        "lot": "SaaS",
        "phoneSupport": True,
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert result == {
        "dmagg_lot": "SaaS",
        "dmtext_lot": "SaaS",
        "dmfilter_lot": "SaaS",
        "dmfilter_phoneSupport": True,
    }


def test_should_make__match_array_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "publicSectorNetworksTypes": ["Internet", "PSN"],
        "serviceCategories": ["One", "Two", "Three"],
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert result == {
        "dmagg_lot": "SaaS",
        "dmagg_serviceCategories": ["One", "Two", "Three"],
        "dmfilter_lot": "SaaS",
        "dmfilter_publicSectorNetworksTypes": ["Internet", "PSN"],
        "dmfilter_serviceCategories": ["One", "Two", "Three"],
        "dmtext_lot": "SaaS",
        "dmtext_serviceCategories": ["One", "Two", "Three"],
    }


def test_should_ignore_non_filter_and_non_text_fields(services_mapping):
    request = {
        "lot": "SaaS",
        "ignore": "Unchanged",
    }

    result = convert_request_json_into_index_json(services_mapping, request)
    assert result == {
        "dmagg_lot": "SaaS",
        "dmtext_lot": "SaaS",
        "dmfilter_lot": "SaaS",
    }


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
        {
            "set_conditionally": {
                "field": "supplierName",
                "any_of": [
                    "foo",
                ],
                "set_value": [
                    "bar"
                ]
            }
        }
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
                "target_field": "serviceCategories",
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
        "dmagg_serviceCategories": ["bar"],
        "dmtext_supplierName": ["foo"],
        "dmtext_serviceCategories": ["bar"],
        "dmfilter_serviceCategories": ["bar"],
    }


class TestSetConditionally():
    def test_updates_source_field_when_no_target(self, services_mapping):
        services_mapping.transform_fields = [
            {
                "set_conditionally": {
                    "field": "supplierName",
                    "any_of": [
                        "Red",
                        "Orange",
                        "Yellow"
                    ],
                    "set_value": [
                        "Green"
                    ]
                }
            }
        ]

        request = {
            "supplierName": ["Red"],
        }

        result = convert_request_json_into_index_json(services_mapping, request)

        assert result == {
            "dmtext_supplierName": ["Green"]
        }

    def test_updates_target_field(self, services_mapping):
        services_mapping.transform_fields = [
            {
                "set_conditionally": {
                    "field": "supplierName",
                    "target_field": "serviceCategories",
                    "any_of": [
                        "Blue",
                        "Indigo",
                        "Violet"
                    ],
                    "set_value": [
                        "Pink"
                    ]
                }
            }
        ]

        request = {
            "supplierName": ["Violet"],
            "serviceCategories": ["Brown"]
        }

        result = convert_request_json_into_index_json(services_mapping, request)

        assert result == {
            "dmagg_serviceCategories": ["Pink"],
            "dmtext_supplierName": ["Violet"],
            "dmtext_serviceCategories": ["Pink"],
            "dmfilter_serviceCategories": ["Pink"],
        }

    def test_creates_target_field_if_it_does_not_exist(self, services_mapping):
        services_mapping.transform_fields = [
            {
                "set_conditionally": {
                    "field": "supplierName",
                    "target_field": "serviceCategories",
                    "any_of": [
                        "Blue",
                        "Indigo",
                        "Violet"
                    ],
                    "set_value": [
                        "Pink"
                    ]
                }
            }
        ]

        request = {
            "supplierName": ["Violet"],
        }

        result = convert_request_json_into_index_json(services_mapping, request)

        assert result == {
            "dmagg_serviceCategories": ["Pink"],
            "dmtext_supplierName": ["Violet"],
            "dmtext_serviceCategories": ["Pink"],
            "dmfilter_serviceCategories": ["Pink"],
        }

    def test_does_not_update_if_value_does_not_match(self, services_mapping):
        services_mapping.transform_fields = [
            {
                "set_conditionally": {
                    "field": "supplierName",
                    "any_of": [
                        "Grey",
                        "Black",
                        "White"
                    ],
                    "set_value": [
                        "Gold"
                    ]
                }
            }
        ]

        request = {
            "supplierName": ["Silver"],
        }

        result = convert_request_json_into_index_json(services_mapping, request)

        assert result == {
            "dmtext_supplierName": ["Silver"],
        }

    def test_works_if_source_field_is_a_string(self, services_mapping):
        services_mapping.transform_fields = [
            {
                "set_conditionally": {
                    "field": "supplierName",
                    "any_of": [
                        "Red",
                        "Orange",
                        "Yellow"
                    ],
                    "set_value": "Green"
                }
            }
        ]

        request = {
            "supplierName": "Orange",
        }

        result = convert_request_json_into_index_json(services_mapping, request)

        assert result == {
            "dmtext_supplierName": "Green"
        }


def test_service_id_hash_added_if_id_present(services_mapping):
    request = {
        "id": "999999999",
    }

    result = convert_request_json_into_index_json(services_mapping, request)

    assert result == {
        "dmtext_id": "999999999",
        "sortonly_serviceIdHash": "bb421fa35db885ce507b0ef5c3f23cb09c62eb378fae3641c165bdf4c0272949",
    }
