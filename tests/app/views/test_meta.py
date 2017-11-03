import json
from ..helpers import BaseApplicationTest


class TestMeta(BaseApplicationTest):
    def test_home(self):
        with self.app.app_context():
            response = self.client.get('/')
            response_data = json.loads(response.get_data())

            assert response.status_code == 200
            assert 'links' in response_data
            assert set(response_data['field-mappings']) == set(('services', ))
