from __future__ import absolute_import

import pytest
import os
import mock
import json

import app.mapping


with open(os.path.join(os.path.dirname(__file__), 'fixtures/mappings/services.json')) as f:
    _services_mapping_definition = json.load(f)


@pytest.fixture(scope="function")
def services_mapping():
    """Fixture that provides an Elastic Search mapping, for unit testing functions that expect to be passed one."""
    return app.mapping.Mapping(_services_mapping_definition, 'services')


@pytest.fixture(scope="module", autouse=True)
def services_mapping_definition():
    """Fixture that patches load_mapping_definition, to ensure our mapping fixture is used wherever an index is
    created."""
    with mock.patch('app.mapping.load_mapping_definition') as mock_definition_loader:
        mock_definition_loader.return_value = _services_mapping_definition
        yield mock_definition_loader.return_value
