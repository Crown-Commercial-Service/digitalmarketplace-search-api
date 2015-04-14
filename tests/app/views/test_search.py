from nose.tools import assert_equal

from ..helpers import BaseApplicationTest, get_json_from_response


class TestSearch(BaseApplicationTest):
    def test_should_be_able_create_and_delete_index(self):
        response = self.client.put('/index-to-create')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["message"],
                     "acknowledged")

        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 200)

        response = self.client.delete('/index-to-create')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["message"],
                     "acknowledged")

        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 404)

    def test_should_not_be_able_create_index_twice(self):
        self.client.put('/index-to-create')

        response = self.client.put('/index-to-create')
        assert_equal(response.status_code, 400)
        assert_equal(
            get_json_from_response(response)["message"],
            "IndexAlreadyExistsException[[index-to-create] already exists]")

    def test_should_not_be_able_delete_index_twice(self):
        self.client.put('/index-to-create')
        self.client.delete('/index-to-create')
        response = self.client.delete('/index-to-create')
        assert_equal(response.status_code, 404)
        assert_equal(get_json_from_response(response)["message"],
                     "IndexMissingException[[index-to-create] missing]")

    def test_should_return_404_if_no_index(self):
        response = self.client.get('/index-does-not-exist/status')
        assert_equal(response.status_code, 404)
        assert_equal(get_json_from_response(response)["message"],
                     "IndexMissingException[[index-does-not-exist] missing]")
