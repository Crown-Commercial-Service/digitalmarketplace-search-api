"""
Tests for the application infrastructure
"""
from flask import json
from .helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def test_index(self):
        response = self.client.get('/')
        assert 200 == response.status_code
        assert 'links' in json.loads(response.get_data())

    def test_404(self):
        response = self.client.get('/not-found')
        assert 404 == response.status_code

    def test_202(self):
        response = self.client.get('/search?q=email')
        assert 202 == response.status_code
