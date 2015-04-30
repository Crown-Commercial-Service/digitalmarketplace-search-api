from flask import json
import time
from nose.tools import assert_equal

from ..helpers import BaseApplicationTest
from app.main.services.process_request_json import process


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
    def test_should_return_service_on_keyword_search(self):
        service = default_service()
        self.client.post(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        time.sleep(5)
        response = self.client.get(
            '/index-to-create/services/search?q=serviceName')
        assert_equal(response.status_code, 200)
        assert_equal(get_json_from_response(response)["search"]["total"], 1)


class TestFetchById(BaseApplicationTest):
    def test_should_return_404_if_no_service(self):
        response = self.client.get(
            '/index-to-create/services/100')

        assert_equal(response.status_code, 404)

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

        cases = [
            "lot",
            "serviceName",
            "serviceSummary",
            "serviceBenefits",
            "serviceFeatures",
            "serviceTypes",
            "supplierName",
            "freeOption",
            "trialOption",
            "minimumContractPeriod",
            "supportForThirdParties",
            "selfServiceProvisioning",
            "datacentresEUCode",
            "dataBackupRecovery",
            "dataExtractionRemoval",
            "networksConnected",
            "apiAccess",
            "openStandardsSupported",
            "openSource",
            "persistentStorage",
            "guaranteedResources",
            "elasticCloud"
        ]

        for key in cases:
            assert_equal(
                data['services']["_source"][key],
                service["service"][key], key)

    def test_service_should_have_all_exact_match_fields(self):
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

        cases = [
            "lot",
            "serviceTypes",
            "freeOption",
            "trialOption",
            "minimumContractPeriod",
            "supportForThirdParties",
            "selfServiceProvisioning",
            "datacentresEUCode",
            "dataBackupRecovery",
            "dataExtractionRemoval",
            "networksConnected",
            "apiAccess",
            "openStandardsSupported",
            "openSource",
            "persistentStorage",
            "guaranteedResources",
            "elasticCloud"
        ]

        for key in cases:
            assert_equal(
                data['services']["_source"][key + "Exact"],
                process(service["service"], key), key)


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


def default_service():
    return {
        "service": {
            "id": "id",
            "lot": "LoT",
            "serviceName": "serviceName",
            "serviceSummary": "serviceSummary",
            "serviceBenefits": "serviceBenefits",
            "serviceFeatures": "serviceFeatures",
            "serviceTypes": ["serviceTypes"],
            "supplierName": "Supplier Name",
            "freeOption": True,
            "trialOption": True,
            "minimumContractPeriod": "Month",
            "supportForThirdParties": True,
            "selfServiceProvisioning": True,
            "datacentresEUCode": True,
            "dataBackupRecovery": True,
            "dataExtractionRemoval": True,
            "networksConnected": ["PSN", "PNN"],
            "apiAccess": True,
            "openStandardsSupported": True,
            "openSource": True,
            "persistentStorage": True,
            "guaranteedResources": True,
            "elasticCloud": True
        }
    }


def get_json_from_response(response):
    return json.loads(response.get_data())
