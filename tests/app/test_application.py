"""
Tests for the application infrastructure
"""
import gzip

from flask import json

from tests.helpers import BaseApplicationTest, BaseApplicationTestWithIndex


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


class TestGzip(BaseApplicationTestWithIndex):
    def setup(self):
        super().setup()
        for c in "abcdefghijklmnopqrstuvwxyz1234567890":
            # create a bunch of indexes with quite long names so we definitely have a response from the "/" route
            # that is > the minimum gzipped size limit
            self.create_index(index_name=f"test-{c*180}")

    def test_gzip(self):
        response = self.client.get('/', headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") == "gzip"
        # check the un-gzipped content can successfully be read as json
        assert json.loads(gzip.decompress(response.data))
