
import json
from tests.helpers import BaseApplicationTestWithIndex

from app import elasticsearch_client


class TestMeta(BaseApplicationTestWithIndex):

    def setup(self):
        super().setup()
        with self.app.app_context():
            self.client.put('/index-alias', data=json.dumps({
                "type": "alias",
                "target": "test-index",
            }), content_type="application/json")

            elasticsearch_client.indices.create(
                index=".dot-index",
                body=json.dumps({"mappings": {"mapping": {}}})
            )
            self.client.put('/dot-index-alias', data=json.dumps({
                "type": "alias",
                "target": ".dot-index",
            }), content_type="application/json")

    def teardown(self):
        with self.app.app_context():
            elasticsearch_client.indices.delete(".dot-index")
            elasticsearch_client.indices.delete_alias(name="index-alias", index="test-index")
        super().teardown()

    def test_home(self):
        response = self.client.get('/')
        response_data = response.json

        assert response.status_code == 200
        assert {"href": "http://localhost/test-index/services/search",
                "rel": "query.gdm.index",
                } in response_data['links']
        assert {"href": "http://localhost/index-alias/services/search",
                "rel": "query.gdm.alias",
                } in response_data['links']
        assert frozenset(response_data['field-mappings']) == frozenset((
            'services',
            'briefs-digital-outcomes-and-specialists-2',
            'services-g-cloud-10',
            'services-g-cloud-11',
            'services-g-cloud-12',
        ))

    def test_excludes_dot_indices_with_aliases(self):

        response = self.client.get('/')

        assert response.status_code == 200
        assert b"dot-index" not in response.data
