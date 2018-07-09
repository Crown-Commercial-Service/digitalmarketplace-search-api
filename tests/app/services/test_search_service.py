import json
import mock

from elasticsearch import TransportError

from ..helpers import BaseApplicationTestWithIndex


class TestCoreSearchAndAggregate(BaseApplicationTestWithIndex):

    @mock.patch('app.main.services.search_service.es')
    def test_correct_exception_is_logged_with_info_attribute(self, es_mock):
        es_mock.search.side_effect = TransportError(500, 'NewConnectionError', 'Temporary failure in name resolution')

        response = self.client.get('/index-to-create/services/search')
        data = json.loads(response.get_data())

        assert response.status_code == 500
        assert data['error'] == 'Temporary failure in name resolution'

    @mock.patch('app.main.services.search_service.es')
    def test_correct_exception_is_logged_without_info_attribute(self, es_mock):
        es_mock.search.side_effect = TransportError(500, 'NewConnectionError', None)

        response = self.client.get('/index-to-create/services/search')
        data = json.loads(response.get_data())

        assert response.status_code == 500
        assert data['error'] is None
