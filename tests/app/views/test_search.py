import mock

from app.main.services.process_request_json import process_values_for_matching
from app.main.services import search_service
from flask import json
from nose.tools import assert_equal, assert_in

from ..helpers import BaseApplicationTest, default_service


class TestSearchIndexes(BaseApplicationTest):
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

    def test_creating_existing_index_updates_mapping(self):
        self.client.put('/index-to-create')

        with self.app.app_context():
            with mock.patch(
                'app.main.services.search_service.es.indices.put_mapping'
            ) as es_mock:
                response = self.client.put('/index-to-create')

        assert_equal(response.status_code, 200)
        assert_equal("acknowledged", get_json_from_response(response)["message"])
        es_mock.assert_called_with(
            index='index-to-create',
            doc_type='services',
            body=mock.ANY
        )

    def test_should_not_be_able_delete_index_twice(self):
        self.client.put('/index-to-create')
        self.client.delete('/index-to-create')
        response = self.client.delete('/index-to-create')
        assert_equal(response.status_code, 404)
        assert_equal("IndexMissingException[[index-to-create] missing]"
                     in get_json_from_response(response)["message"], True)

    def test_should_return_404_if_no_index(self):
        response = self.client.get('/index-does-not-exist/status')
        assert_equal(response.status_code, 404)
        assert_equal(
            "IndexMissingException[[index-does-not-exist] missing]" in
            get_json_from_response(response)["status"],
            True)


class TestIndexingDocuments(BaseApplicationTest):
    def setup(self):
        super(TestIndexingDocuments, self).setup()
        self.client.put('/index-to-create')

    def test_should_index_a_document(self):
        service = default_service()

        response = self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

        with self.app.app_context():
            search_service.refresh('index-to-create')
        response = self.client.get('/index-to-create/status')
        assert_equal(response.status_code, 200)
        assert_equal(
            get_json_from_response(response)["status"]["num_docs"],
            1)

    def test_should_index_a_document_with_missing_fields(self):
        service = default_service()
        del service["service"]["serviceName"]

        response = self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

    def test_should_index_a_document_with_extra_fields(self):
        service = default_service()
        service["service"]["randomField"] = "some random"

        response = self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

    def test_should_index_a_document_with_incorrect_types(self):
        service = default_service()
        service["service"]["serviceName"] = 123

        response = self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)

    def test_should_index_a_document_with_no_service_types(self):
        service = default_service()
        service["service"]["serviceName"] = 123
        del service["service"]["serviceTypes"]

        response = self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

        assert_equal(response.status_code, 200)


class TestSearchEndpoint(BaseApplicationTest):
    def setup(self):
        super(TestSearchEndpoint, self).setup()
        with self.app.app_context():
            services = create_services(10)
            for service in services:
                self.client.put(
                    '/index-to-create/services/'
                    + str(service["service"]["id"]),
                    data=json.dumps(service),
                    content_type='application/json')
            search_service.refresh('index-to-create')

    def test_should_return_service_on_id(self):
        service = default_service()
        self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json')

    def test_should_return_service_on_keyword_search(self):
        with self.app.app_context():
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)

    def test_should_get_services_up_to_page_size(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName'
            )
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["services"]), 5)

    def test_should_get_pagination_links(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '3'

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=2')
            response_json = get_json_from_response(response)

            assert_equal(response.status_code, 200)
            assert_in("page=1", response_json['links']['prev'])
            assert_in("page=3", response_json['links']['next'])

    def test_should_get_services_next_page_of_services(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=5')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["services"]), 5)

    def test_should_get_no_services_on_out_of_bounds_from(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=3')
            assert_equal(response.status_code, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["services"]), 0)

    def test_should_get_400_response__on_negative_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=-1')
            assert_equal(response.status_code, 400)

    def test_should_get_400_response__on_non_numeric_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=foo')
            assert_equal(response.status_code, 400)

    def test_highlighting_should_use_defined_html_tags(self):
        with self.app.app_context():
            service = default_service()
            service["service"]['serviceSummary'] = \
                u"Accessing, storing and retaining email"
            highlighted_summary = \
                "Accessing, <em class='search-result-highlighted-text'>" +\
                "storing</em> and retaining email"
            self.client.put(
                '/index-to-create/services/' + str(service["service"]["id"]),
                data=json.dumps(service),
                content_type='application/json')
            search_service.refresh('index-to-create')

            response = self.client.get(
                '/index-to-create/services/search?q=storing')
            assert_equal(response.status_code, 200)
            search_results = get_json_from_response(
                response
            )["services"]
            assert_equal(
                search_results[0]["highlight"]["serviceSummary"][0],
                highlighted_summary
            )

    def test_highlighting_should_escape_html(self):
        service = default_service(
            serviceSummary="accessing, storing <h1>and retaining</h1> email"
        )

        self.client.put(
            '/index-to-create/services/%s' % service["service"]["id"],
            data=json.dumps(service), content_type='application/json')

        with self.app.app_context():
            search_service.refresh('index-to-create')

        response = self.client.get(
            '/index-to-create/services/search?q=storing'
        )
        assert_equal(response.status_code, 200)
        search_results = get_json_from_response(response)["services"]
        assert_equal(
            search_results[0]["highlight"]["serviceSummary"][0],
            "accessing, <em class='search-result-highlighted-text'>" +
            "storing</em> &lt;h1&gt;and retaining&lt;&#x2F;h1&gt; email"
        )


class TestFetchById(BaseApplicationTest):
    def test_should_return_404_if_no_service(self):
        response = self.client.get(
            '/index-to-create/services/100')

        assert_equal(response.status_code, 404)

    def test_should_return_service_by_id(self):
        service = default_service()
        self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')

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
            # (indexed name, original name)
            ("filter_lot", "lot"),
            ("serviceName", "serviceName"),
            ("serviceSummary", "serviceSummary"),
            ("serviceBenefits", "serviceBenefits"),
            ("serviceFeatures", "serviceFeatures"),
            ("serviceTypes", "serviceTypes"),
            ("filter_serviceTypes", "serviceTypes"),
            ("supplierName", "supplierName"),
            ("filter_freeOption", "freeOption"),
            ("filter_trialOption", "trialOption"),
            ("filter_minimumContractPeriod", "minimumContractPeriod"),
            ("filter_supportForThirdParties", "supportForThirdParties"),
            ("filter_selfServiceProvisioning", "selfServiceProvisioning"),
            ("filter_datacentresEUCode", "datacentresEUCode"),
            ("filter_dataBackupRecovery", "dataBackupRecovery"),
            ("filter_dataExtractionRemoval", "dataExtractionRemoval"),
            ("filter_networksConnected", "networksConnected"),
            ("filter_apiAccess", "apiAccess"),
            ("filter_openStandardsSupported", "openStandardsSupported"),
            ("filter_openSource", "openSource"),
            ("filter_persistentStorage", "persistentStorage"),
            ("filter_guaranteedResources", "guaranteedResources"),
            ("filter_elasticCloud", "elasticCloud")
        ]

        # filter fields are processed (lowercase etc)
        # and also have a new key (filter_FIELDNAME)
        for key in cases:
            original = service["service"][key[1]]
            indexed = data['services']["_source"][key[0]]
            if key[0].startswith("filter"):
                original = process_values_for_matching(service["service"][key[1]])
            assert_equal(original, indexed)

    def test_service_should_have_all_exact_match_fields(self):
        service = default_service()
        self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')
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
                data['services']["_source"]["filter_" + key],
                process_values_for_matching(service["service"][key]))


class TestDeleteById(BaseApplicationTest):
    def test_should_delete_service_by_id(self):
        service = default_service()
        self.client.put(
            '/index-to-create/services/' + str(service["service"]["id"]),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')
        response = self.client.delete(
            '/index-to-create/services/' + str(service["service"]["id"]))

        data = get_json_from_response(response)
        assert_equal(response.status_code, 200)
        assert_equal(data['message']['found'], True)

        response = self.client.get(
            '/index-to-create/services/' + str(service["service"]["id"]))
        data = get_json_from_response(response)
        assert_equal(response.status_code, 404)
        assert_equal(data['message']['found'], False)

    def test_should_return_404_if_no_service(self):
        self.client.put('/index-to-create')

        response = self.client.delete(
            '/index-to-create/delete/100')

        data = get_json_from_response(response)
        assert_equal(response.status_code, 404)
        assert_equal(data['message']['found'], False)


def create_services(number_of_services):
    services = []
    for i in range(number_of_services):
        service = default_service(id=str(i))
        services.append(service)

    return services


def get_json_from_response(response):
    return json.loads(response.get_data())
