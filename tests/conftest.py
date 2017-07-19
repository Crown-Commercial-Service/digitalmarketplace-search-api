from __future__ import absolute_import

import pytest
import os
import mock
import json

import app.mapping


with open(os.path.join(os.path.dirname(__file__), 'fixtures/mappings/services.json')) as f:
    _services_mapping_definition = json.load(f)


@pytest.fixture(scope="session", autouse=True)
def services_mapping_dummy_patch():
    """
    Failsafe fixture, to ensure app.mapping.get_services_mapping is never called.

    This exists to prevent confusion when errors are caused due to inconsistency between functions that use the
    services_mapping fixture (below), and test module/class fixtures/setup, which will need to manually ensure that the
    function is patched. See tests.app.views.test_search_queries.dummy_services for an example of such manual patching.

    The proper services_mapping fixture cannot be session or module scoped because test functions frequently make custom
    modifications to the mapping, which must not be allowed to leak between tests.

    """
    with mock.patch('app.mapping.get_services_mapping') as mock_services_mapping_getter:
        mock_services_mapping_getter.side_effect = Exception('Unmocked get_services_mapping call.')
        yield None


@pytest.fixture(scope="function")
def services_mapping():
    """Fixture that provides a services mapping, and patches it into the global singleton getter."""

    with mock.patch('app.mapping.get_services_mapping') as mock_services_mapping_getter:
        mock_services_mapping_getter.return_value = app.mapping.Mapping(_services_mapping_definition, 'services')
        yield mock_services_mapping_getter.return_value
