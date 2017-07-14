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
    """Provide a services mapping fixture, and patch it into the global singleton getter."""

    mock_services_mapping_getter_patch = mock.patch('app.mapping.get_services_mapping')
    mock_services_mapping_getter = mock_services_mapping_getter_patch.start()
    mock_services_mapping_getter.return_value = app.mapping.Mapping(_services_mapping_definition, 'services')

    yield mock_services_mapping_getter.return_value

    mock_services_mapping_getter_patch.stop()
