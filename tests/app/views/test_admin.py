import pytest
from flask import json

from tests.app.helpers import BaseApplicationTest, assert_response_status, get_json_from_response


pytestmark = pytest.mark.usefixtures("services_mapping")


class TestSearchIndexes(BaseApplicationTest):
    def test_should_be_able_create_and_delete_index(self):
        response = self.create_index()
        assert_response_status(response, 200)
        assert get_json_from_response(response)["message"] == "acknowledged"

        response = self.client.get('/index-to-create')
        assert_response_status(response, 200)

        response = self.client.delete('/index-to-create')
        assert_response_status(response, 200)
        assert get_json_from_response(response)["message"] == "acknowledged"

        response = self.client.get('/index-to-create')
        assert_response_status(response, 404)

    def test_should_be_able_to_create_aliases(self):
        self.create_index()
        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        assert_response_status(response, 200)
        assert get_json_from_response(response)["message"] == "acknowledged"

    def test_should_not_be_able_to_delete_aliases(self):
        self.create_index()
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        response = self.client.delete('/index-alias')

        assert_response_status(response, 400)
        assert get_json_from_response(response)["error"] == "Cannot delete alias 'index-alias'"

    def test_should_not_be_able_to_delete_index_with_alias(self):
        self.create_index()
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        response = self.client.delete('/index-to-create')

        assert_response_status(response, 400)
        assert (
            get_json_from_response(response)["error"] ==
            "Index 'index-to-create' is aliased as 'index-alias' and cannot be deleted"
        )

    def test_cant_create_alias_for_missing_index(self):
        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        assert_response_status(response, 404)
        assert get_json_from_response(response)["error"].startswith(
            'index_not_found_exception: no such index')

    def test_cant_replace_index_with_alias(self):
        self.create_index()
        response = self.client.put('/index-to-create', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        assert_response_status(response, 400)

        expected_string = (
            'invalid_alias_name_exception: Invalid alias name [index-to-create], an index exists with the same name '
            'as the alias (index-to-create)'
        )
        assert get_json_from_response(response)["error"] == expected_string

    def test_can_update_alias(self):
        self.create_index()
        self.create_index('index-to-create-2')
        self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create"
        }), content_type="application/json")

        response = self.client.put('/index-alias', data=json.dumps({
            "type": "alias",
            "target": "index-to-create-2"
        }), content_type="application/json")

        assert_response_status(response, 200)
        status = get_json_from_response(self.client.get('/_all'))["status"]
        assert status['index-to-create']['aliases'] == []
        assert status['index-to-create-2']['aliases'] == ['index-alias']

    def test_creating_existing_index_fails(self):
        self.create_index()

        response = self.create_index(expect_success=False)

        assert_response_status(response, 400)
        assert get_json_from_response(response)["error"].startswith("index_already_exists_exception:")

    def test_should_not_be_able_delete_index_twice(self):
        self.create_index()
        self.client.delete('/index-to-create')
        response = self.client.delete('/index-to-create')
        assert_response_status(response, 404)
        assert get_json_from_response(response)["error"] == 'index_not_found_exception: no such index (index-to-create)'

    def test_should_return_404_if_no_index(self):
        response = self.client.get('/index-does-not-exist')
        assert_response_status(response, 404)
        assert (
            get_json_from_response(response)["error"] ==
            "index_not_found_exception: no such index (index-does-not-exist)"
        )

    def test_bad_mapping_name_gives_400(self):
        response = self.client.put('/index-to-create', data=json.dumps({
            "type": "index",
            "mapping": "some-bad-mapping"
        }), content_type="application/json")

        assert_response_status(response, 400)
        assert get_json_from_response(response)["error"] == "Mapping definition named 'some-bad-mapping' not found."
