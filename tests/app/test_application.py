"""
Tests for the application infrastructure
"""
import mock
import pytest

from flask import json
from elasticsearch.exceptions import ConnectionError

from .helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def test_index(self):
        response = self.client.get('/')
        assert 200 == response.status_code
        assert 'links' in json.loads(response.get_data())

    def test_404(self):
        response = self.client.get('/index/type/search')
        assert 404 == response.status_code

    def test_bearer_token_is_required(self):
        self.do_not_provide_access_token()
        response = self.client.get('/')
        assert 401 == response.status_code
        assert 'WWW-Authenticate' in response.headers

    def test_invalid_bearer_token_is_required(self):
        self.do_not_provide_access_token()
        response = self.client.get(
            '/',
            headers={'Authorization': 'Bearer invalid-token'})
        assert 403 == response.status_code

    def test_ttl_is_not_set(self):
        response = self.client.get('/')
        assert response.cache_control.max_age is None

    @mock.patch('elasticsearch.transport.Urllib3HttpConnection.perform_request', side_effect=ConnectionError(500))
    def test_elastic_search_client_performs_retries_on_connection_error(self, perform_request):
        with pytest.raises(ConnectionError):
            self.client.get('/')

        # FlaskElasticsearch attaches the es client to the context in flask_elasticsearch.py
        from flask import _app_ctx_stack

        assert perform_request.call_count == 1 + _app_ctx_stack.top.elasticsearch.transport.max_retries
        assert perform_request.call_count == 1 + 3
