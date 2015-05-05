from flask import json
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
        service = default_service()

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

        time.sleep(5)  # needs time to propagate???
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

    def test_should_index_a_document_with_no_service_types(self):
        service = default_service()
        service["service"]["serviceName"] = 123
        del service["service"]["serviceTypes"]

        response = self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)


# TODO write a load of queries into here for the various fields
class TestSearchQueries(BaseApplicationTest):
    def setup(self):
        super(TestSearchQueries, self).setup()
        with self.app.app_context():
            services = create_services(10)
            for service in services:
                self.client.post(
                    '/index-to-create/services/'
                    + str(service["service"]["id"]),
                    data=json.dumps(service),
                    content_type='application/json')
            time.sleep(5)

    def test_should_return_service_on_keyword_search(self):
        with self.app.app_context():
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["search"]["total"], 10)

    def test_should_get_services_up_to_page_size(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName'
            )
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["search"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["search"]["services"]), 5)

    def test_should_get_services_next_page_of_services(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=5')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["search"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["search"]["services"]), 5)

    def test_should_get_no_services_on_out_of_bounds_from(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=10')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["search"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["search"]["services"]), 0)

    def test_should_get_no_services_on_out_of_bounds_from(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=10')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["search"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["search"]["services"]), 0)

    def test_should_get_400_response__on_negative_index(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=-10')
            assert_equal(response.status_code, 400)


class TestFetchById(BaseApplicationTest):
    def test_should_return_service_by_id(self):
        service = default_service()
        self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json'
        )

        time.sleep(5)
        response = self.client.get(
            '/index-to-create/services/' + str(service["service"]["id"]))

        data = get_json_from_response(response)
        assert_equal(response.status_code, 200)
        assert_equal(
            data['services']["_id"],
            str(service["service"]["id"]))
        assert_equal(
            data['services']["_source"]["id"],
            str(service["service"]["id"]))
        assert_equal(
            data['services']["_source"]["lot"],
            service["service"]["lot"])
        assert_equal(
            data['services']["_source"]["serviceBenefits"],
            service["service"]["serviceBenefits"])
        assert_equal(
            data['services']["_source"]["serviceFeatures"],
            service["service"]["serviceFeatures"])
        assert_equal(
            data['services']["_source"]["serviceName"],
            service["service"]["serviceName"])
        assert_equal(
            data['services']["_source"]["serviceSummary"],
            service["service"]["serviceSummary"])
        assert_equal(
            data['services']["_source"]["serviceTypes"],
            service["service"]["serviceTypes"])
        assert_equal(
            data['services']["_source"]["serviceTypesExact"],
            ['servicetypes'])
        assert_equal(
            data['services']["_source"]["supplierName"],
            service["service"]["supplierName"])

    def test_should_return_404_if_no_service(self):
        response = self.client.get(
            '/index-to-create/services/100')

        assert_equal(response.status_code, 404)


class TestDeleteById(BaseApplicationTest):
    def test_should_delete_service_by_id(self):
        service = default_service()
        self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json'
        )

        time.sleep(5)
        response = self.client.delete(
            '/index-to-create/services/' + str(service["service"]["id"]))

        data = get_json_from_response(response)
        assert_equal(response.status_code, 200)
        assert_equal(data['services']['found'], True)

        response = self.client.get(
            '/index-to-create/services/' + str(service["service"]["id"]))
        data = get_json_from_response(response)
        assert_equal(response.status_code, 404)
        assert_equal(data['services']['found'], False)

    def test_should_return_404_if_no_service(self):
        self.client.put('/index-to-create')

        response = self.client.delete(
            '/index-to-create/delete/100')

        data = get_json_from_response(response)
        assert_equal(response.status_code, 404)
        assert_equal(data['services']['found'], False)


def create_services(number_of_services):
    services = []
    for i in range(number_of_services):
        service = default_service()
        service["service"]["id"] = str(i)
        services.append(service)

    return services


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
