import mock
import pytest
from flask import json
from urllib3.exceptions import NewConnectionError

from app.main.services import search_service
from tests.app.helpers import BaseApplicationTestWithIndex, make_search_api_url, assert_response_status, \
    get_json_from_response


pytestmark = pytest.mark.usefixtures("services_mapping")


class TestIndexingDocuments(BaseApplicationTestWithIndex):
    EXAMPLE_CONNECTION_ERROR = (
        '<urllib3.connection.HTTPConnection object at 0x107626588>: '
        'Failed to establish a new connection: [Errno 61] Connection refused'
    )

    def test_should_index_a_document(self, default_service):
        service = default_service

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')

        assert_response_status(response, 200)

        with self.app.app_context():
            search_service.refresh('index-to-create')
        response = self.client.get('/index-to-create')
        assert_response_status(response, 200)
        assert get_json_from_response(response)["status"]["num_docs"] == 1

    @mock.patch('app.main.views.update.index')
    @mock.patch('app.main.services.response_formatters.current_app')
    @pytest.mark.parametrize('error_status_code', ['N/A', 'something_other_than_N/A'])
    def test_index_document_handles_connection_error(self, current_app, index, error_status_code, default_service):
        index.return_value = (NewConnectionError('', self.EXAMPLE_CONNECTION_ERROR), error_status_code)
        service = default_service

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )
        assert_response_status(response, 500)
        current_app.logger.error.assert_called_once_with(
            f'API response error: ": {self.EXAMPLE_CONNECTION_ERROR}" Unexpected status code: "{error_status_code}"'
        )

    def test_should_index_a_document_with_missing_fields(self, default_service):
        service = default_service
        del service.get('document', service.get('service'))["serviceName"]

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')

        assert_response_status(response, 200)

    def test_should_index_a_document_with_extra_fields(self, default_service):
        service = default_service
        service.get('document', service.get('service'))["randomField"] = "some random"

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')

        assert_response_status(response, 200)

    def test_should_index_a_document_with_incorrect_types(self, default_service):
        service = default_service
        service.get('document', service.get('service'))["serviceName"] = 123

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')

        assert_response_status(response, 200)

    def test_should_index_a_document_with_no_service_types(self, default_service):
        service = default_service
        service.get('document', service.get('service'))["serviceName"] = 123
        del service.get('document', service.get('service'))["serviceCategories"]

        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')

        assert_response_status(response, 200)

    def test_should_raise_400_on_bad_doc_type(self, default_service):
        response = self.client.put(
            make_search_api_url(default_service, type_name='some-bad-type'),
            data=json.dumps(default_service),
            content_type='application/json')

        assert_response_status(response, 400)


class TestDeleteById(BaseApplicationTestWithIndex):
    def test_should_delete_service_by_id(self, default_service):
        service = default_service
        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')
        response = self.client.delete(make_search_api_url(service),)

        data = get_json_from_response(response)
        assert_response_status(response, 200)
        assert data['message']['found'] is True

        response = self.client.get(make_search_api_url(service),)
        data = get_json_from_response(response)
        assert_response_status(response, 404)
        assert data['error']['found'] is False

    def test_should_return_404_if_no_service(self):
        response = self.client.delete(
            '/index-to-create/delete/100')

        data = get_json_from_response(response)
        assert_response_status(response, 404)
        assert data['error']['found'] is False
