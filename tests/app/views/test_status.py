import json

import mock
from elasticsearch import TransportError

from tests.helpers import BaseApplicationTest


class TestStatus(BaseApplicationTest):
    def test_status(self):
        with self.app.app_context():
            response = self.client.get('/_status')

            assert response.status_code == 200

    def test_status_returns_json(self):
        with self.app.app_context():
            response = self.client.get('/_status')

            assert response.json

    def test_status_includes_meta_information(self):
        with self.app.app_context():
            response = self.client.get('/_status')

            for index, details in response.json["es_status"].items():
                if not index.startswith("."):
                    assert details["mapping_generated_from_framework"]
                    assert details["mapping_version"]
                    assert details["max_result_window"]

    def test_should_return_200_from_elb_status_check(self):
        status_response = self.client.get('/_status?ignore-dependencies')
        assert status_response.status_code == 200

    @mock.patch('app.main.services.search_service.es.indices')
    def test_status_when_elasticsearch_is_down(self, indices):
        with self.app.app_context():
            indices.stats.side_effect = TransportError(500, "BARR", "FOO")
            response = self.client.get('/_status')

            assert response.status_code == 500

            data = json.loads(response.data.decode('utf-8'))
            assert data['message'] == ['Error connecting to elasticsearch (status_code: 500, message: FOO)']
