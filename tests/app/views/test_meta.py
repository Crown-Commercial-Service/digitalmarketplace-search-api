import json
from ..helpers import BaseApplicationTestWithIndex


class TestMeta(BaseApplicationTestWithIndex):
    def test_home(self):
        with self.app.app_context():
            self.client.put('/{}'.format('index-alias'), data=json.dumps({
                "type": "alias",
                "target": "index-to-create",
            }), content_type="application/json")

            response = self.client.get('/')
            response_data = json.loads(response.get_data())

            assert response.status_code == 200
            assert {"href": "http://localhost/index-to-create/services/search",
                    "rel": "query.gdm.index",
                    } in response_data['links']
            assert {"href": "http://localhost/index-alias/services/search",
                    "rel": "query.gdm.alias",
                    } in response_data['links']
            assert frozenset(response_data['field-mappings']) == frozenset((
                'services',
                'briefs-digital-outcomes-and-specialists-2',
            ))
