import json

from nose.tools import assert_equal
import mock
from elasticsearch import TransportError

from ..helpers import BaseApplicationTest


class TestStatus(BaseApplicationTest):
    def test_status(self):
        with self.app.app_context():
            response = self.client.get('/_status')

            assert_equal(response.status_code, 200)

    def test_should_return_200_from_elb_status_check(self):
        status_response = self.client.get('/_status?ignore-dependencies')
        assert_equal(200, status_response.status_code)

    @mock.patch('app.main.services.search_service.es.indices')
    def test_status_when_elasticsearch_is_down(self, indices):
        with self.app.app_context():
            indices.status.side_effect = TransportError(500, "BARR", "FOO")
            response = self.client.get('/_status')

            assert_equal(response.status_code, 500)

            data = json.loads(response.data.decode('utf-8'))
            assert_equal(data['es_status']['message'], "FOO")
