import json
import time
from nose.tools import assert_equal

from ..helpers import BaseApplicationTest


class TestSearchIndexes(BaseApplicationTest):
    def test_should_be_able_create_and_delete_index(self):
        response = self.client.put('/index-to-create')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["results"],
                     "acknowledged")

        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 200)

        response = self.client.delete('/index-to-create')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["results"],
                     "acknowledged")

        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 404)

    def test_should_not_be_able_create_index_twice(self):
        self.client.put('/index-to-create')

        response = self.client.put('/index-to-create')
        assert_equal(response.status_code, 400)
        assert_equal(
            get_json_from_response(response)["results"],
            "IndexAlreadyExistsException[[index-to-create] already exists]")

    def test_should_not_be_able_delete_index_twice(self):
        self.client.put('/index-to-create')
        self.client.delete('/index-to-create')
        response = self.client.delete('/index-to-create')
        assert_equal(response.status_code, 404)
        assert_equal(get_json_from_response(response)["results"],
                     "IndexMissingException[[index-to-create] missing]")

    def test_should_return_404_if_no_index(self):
        response = self.client.get('/index-does-not-exist/status')
        assert_equal(response.status_code, 404)
        assert_equal(get_json_from_response(response)["status"],
                     "IndexMissingException[[index-does-not-exist] missing]")


class TestIndexingDocuments(BaseApplicationTest):
    def setup(self):
        super(TestIndexingDocuments, self).setup()
        self.client.put('/index-to-create')

    def test_should_index_a_document(self):
        response = self.client.get('/index-to-create/status')

        assert_equal(response.status_code, 200)
        assert_equal(
            get_json_from_response(response)["status"]["num_docs"],
            0)

        service = default_service()

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

        time.sleep(1)  # needs time to propagate???
        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 200)
        assert_equal(
            get_json_from_response(response)["status"]["num_docs"],
            1)

    def test_should_index_a_document_with_missing_fields(self):
        service = default_service()
        del service["service"]["serviceName"]

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

    def test_should_index_a_document_with_extra_fields(self):
        service = default_service()
        service["service"]["randomField"] = "some random"

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

    def test_should_index_a_document_with_incorrect_types(self):
        service = default_service()
        service["service"]["serviceName"] = 123

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)


# TODO write a load of queries into here for the various fields
class TestSearchQueries(BaseApplicationTest):
    def test_should_return_service_on_keyword_search(self):
        service = default_service()
        self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        time.sleep(1)
        response = self.client.get(
            '/index-to-create/services/search?q=serviceName')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["search"]["total"], 1)


def default_service():
    return {
        "service": {
            "id": "id",
            "lot": "lot",
            "serviceName": "serviceName",
            "serviceSummary": "serviceSummary",
            "serviceBenefits": "serviceBenefits",
            "serviceFeatures": "serviceFeatures",
            "serviceTypes": ["serviceTypes"],
            "supplierName": "Supplier Name"
        }
    }


def get_json_from_response(response):
    return json.loads(response.get_data())