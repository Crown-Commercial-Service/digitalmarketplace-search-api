from __future__ import absolute_import


import pytest
import os
import mock
import json

import app.mapping
from tests.app.helpers import make_standard_service


with open(os.path.join(os.path.dirname(__file__), 'fixtures/mappings/services.json')) as f:
    _services_mapping_definition = json.load(f)


@pytest.fixture(scope="function")
def services_mapping():
    """Fixture that provides an Elastic Search mapping, for unit testing functions that expect to be passed one."""
    return app.mapping.Mapping(_services_mapping_definition, 'services')


@pytest.fixture(scope="module")
def services_mapping_definition():
    """Fixture that patches load_mapping_definition, to ensure our mapping fixture is used wherever an index is
    created."""
    with mock.patch('app.mapping.load_mapping_definition') as mock_definition_loader:
        mock_definition_loader.return_value = _services_mapping_definition
        yield mock_definition_loader.return_value


@pytest.fixture(scope="function", params=['service', 'document'])
def default_service(request):
    """
    A fixture for a service such as might be indexed in the Search API. For now, parameterized so that we can test
    both the old style where the structure had a top-level dictionary key hard-coded to 'service', and the new
    style where we just look for a key 'document', which could be a DOS brief or a G-Cloud service or anything else.
    :return: dict
    """
    service = make_standard_service()
    if request.param != 'document':
        service = {request.param: service['document']}
    return service
