

import pytest
import os
import json

import app.mapping


with open(os.path.join(os.path.dirname(__file__), '../mappings/services.json')) as f:
    _services_mapping_definition = json.load(f)


@pytest.fixture()
def services_mapping():
    """Fixture that provides an Elastic Search mapping, for unit testing functions that expect to be passed one."""
    return app.mapping.Mapping(_services_mapping_definition, 'services')
def make_service(**kwargs):
    service = {
        "id": "id",
        "lot": "LoT",
        "serviceName": "serviceName",
        "serviceDescription": "serviceDescription",
        "serviceBenefits": "serviceBenefits",
        "serviceFeatures": "serviceFeatures",
        "serviceCategories": ["serviceCategories"],
        "supplierName": "Supplier Name",
        "publicSectorNetworksTypes": ["PSN", "PNN"],
    }

    service.update(kwargs)

    return {
        "document": service
    }


@pytest.fixture()
def service():
    """
    A fixture for a service such as might be indexed in the Search API.
    :return: dict
    """
    return make_service()
