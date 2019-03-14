from flask import json

from tests.helpers import BaseApplicationTest


class TestSearchIndexes(BaseApplicationTest):
    def test_should_be_able_create_and_delete_index(self):
        response = self.create_index()
        assert response.status_code == 200
        assert response.json["message"] == "acknowledged"

        response = self.client.get('/test-index')
        assert response.status_code == 200

        response = self.client.delete('/test-index')
        assert response.status_code == 200
        assert response.json["message"] == "acknowledged"

        response = self.client.get('/test-index')
        assert response.status_code == 404

    def test_should_be_able_to_create_aliases(self):
        self.create_index()
        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        assert response.status_code == 200
        assert response.json["message"] == "acknowledged"

    def test_should_not_be_able_to_delete_aliases(self):
        self.create_index()
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        response = self.client.delete('/index-alias')

        assert response.status_code == 400
        assert response.json["error"] == "Cannot delete alias 'index-alias'"

    def test_should_not_be_able_to_delete_index_with_alias(self):
        self.create_index()
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        response = self.client.delete('/test-index')

        assert response.status_code == 400
        assert (
            response.json["error"] ==
            "Index 'test-index' is aliased as 'index-alias' and cannot be deleted"
        )

    def test_cant_create_alias_for_missing_index(self):
        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        assert response.status_code == 404
        assert response.json["error"].startswith(
            'index_not_found_exception: no such index')

    def test_cant_replace_index_with_alias(self):
        self.create_index()
        response = self.client.put('/test-index', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        assert response.status_code == 400

        expected_string = (
            'invalid_alias_name_exception: Invalid alias name [test-index], an index exists with the same name '
            'as the alias (test-index)'
        )
        assert response.json["error"] == expected_string

    def test_can_update_alias(self):
        self.create_index()
        self.create_index('test-index-2')
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index"
        }), content_type="application/json")

        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "test-index-2"
        }), content_type="application/json")

        assert response.status_code == 200
        status = self.client.get('/_all').json["status"]
        assert status['test-index']['aliases'] == []
        assert status['test-index-2']['aliases'] == ['index-alias']

    def test_creating_existing_index_fails(self):
        self.create_index()

        response = self.create_index(expect_success=False)

        assert response.status_code == 400
        assert "already_exists_exception" in response.json["error"]

    def test_should_not_be_able_delete_index_twice(self):
        self.create_index()
        self.client.delete('/test-index')
        response = self.client.delete('/test-index')
        assert response.status_code == 404
        assert response.json["error"] == 'index_not_found_exception: no such index (test-index)'

    def test_should_return_404_if_no_index(self):
        response = self.client.get('/index-does-not-exist')
        assert response.status_code == 404
        assert (
            response.json["error"] ==
            "index_not_found_exception: no such index (index-does-not-exist)"
        )

    def test_bad_mapping_name_gives_400(self):
        response = self.client.put('/test-index', data=json.dumps({
            "type": "index",
            "mapping": "some-bad-mapping"
        }), content_type="application/json")

        assert response.status_code == 400
        assert response.json["error"] == "Mapping definition named 'some-bad-mapping' not found."
