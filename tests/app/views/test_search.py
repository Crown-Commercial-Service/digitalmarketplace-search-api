import mock
import pytest
from flask import json
from nose.tools import assert_equal, assert_in, assert_true
from werkzeug import MultiDict

from app import elasticsearch_client as es
from app.main.services import search_service
from app.main.services.search_service import core_search_and_aggregate
from tests.app.helpers import get_json_from_response
from ..helpers import (BaseApplicationTestWithIndex, assert_response_status,
                       make_search_api_url, make_standard_service)

pytestmark = pytest.mark.usefixtures("services_mapping")


@pytest.mark.usefixtures("services_mapping_definition")
class TestSearchEndpoint(BaseApplicationTestWithIndex):
    def setup(self):
        super(TestSearchEndpoint, self).setup()
        with self.app.app_context():
            services = create_services(10)
            for service in services:
                response = self.client.put(
                    make_search_api_url(service),
                    data=json.dumps(service),
                    content_type='application/json')
                assert response.status_code == 200
            search_service.refresh('index-to-create')

    def _put_into_and_get_back_from_elasticsearch(self, service, query_string):

        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service), content_type='application/json')

        with self.app.app_context():
            search_service.refresh('index-to-create')

        return self.client.get(
            '/index-to-create/services/search?{}'.format(query_string)
        )

    def test_should_return_service_on_id(self, default_service):
        service = default_service
        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')
        assert response.status_code == 200

    def test_should_return_service_on_keyword_search(self):
        with self.app.app_context():
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName')
            assert_response_status(response, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)

    def test_keyword_search_via_alias(self):
        with self.app.app_context():
            self.client.put('/{}'.format('index-alias'), data=json.dumps({
                "type": "alias",
                "target": "index-to-create",
            }), content_type="application/json")
            response = self.client.get(
                '/index-alias/services/search?q=serviceName')
            assert_response_status(response, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)

    def test_should_get_services_up_to_page_size(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName'
            )
            assert_response_status(response, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["documents"]), 5)

    def test_should_get_pagination_links(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '3'

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=2')
            response_json = get_json_from_response(response)

            assert_response_status(response, 200)
            assert_in("page=1", response_json['links']['prev'])
            assert_in("page=3", response_json['links']['next'])

    def test_should_get_services_next_page_of_services(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&from=5')
            assert_response_status(response, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["documents"]), 5)

    def test_should_get_no_services_on_out_of_bounds_from(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=3')
            assert_response_status(response, 200)
            assert_equal(
                get_json_from_response(response)["meta"]["total"], 10)
            assert_equal(
                len(get_json_from_response(response)["documents"]), 0)

    def test_should_get_404_on_massively_out_of_bounds_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '50'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=1000000')
            assert_response_status(response, 404)

    def test_should_get_400_response__on_negative_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=-1')
            assert_response_status(response, 400)

    def test_should_get_400_response__on_non_numeric_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&page=foo')
            assert_response_status(response, 400)

    def test_highlighting_should_use_defined_html_tags(self):
        service = make_standard_service(
            serviceSummary="Accessing, storing and retaining email"
        )
        highlighted_summary = \
            "Accessing, <mark class='search-result-highlighted-text'>storing</mark> and retaining email"

        response = self._put_into_and_get_back_from_elasticsearch(
            service=service,
            query_string='q=storing'
        )
        assert_response_status(response, 200)
        search_results = get_json_from_response(
            response
        )["documents"]
        assert_equal(
            search_results[0]["highlight"]["serviceSummary"][0],
            highlighted_summary
        )

    def test_highlighting_should_escape_html(self):
        service = make_standard_service(
            serviceSummary="accessing, storing <h1>and retaining</h1> email"
        )

        response = self._put_into_and_get_back_from_elasticsearch(
            service=service,
            query_string='q=storing'
        )
        assert_response_status(response, 200)
        search_results = get_json_from_response(response)["documents"]
        assert_equal(
            search_results[0]["highlight"]["serviceSummary"][0],
            "accessing, <mark class='search-result-highlighted-text'>" +
            "storing</mark> &lt;h1&gt;and retaining&lt;&#x2F;h1&gt; email"
        )

    def test_unhighlighted_result_should_escape_html(self):
        service = make_standard_service(
            serviceSummary='Oh <script>alert("Yo");</script>',
            lot='oY'
        )

        response = self._put_into_and_get_back_from_elasticsearch(
            service=service,
            query_string='q=oY'
        )
        assert_response_status(response, 200)
        search_results = get_json_from_response(response)["documents"]
        assert_equal(
            search_results[0]["highlight"]["serviceSummary"][0],
            "Oh &lt;script&gt;alert(&quot;Yo&quot;);&lt;&#x2F;script&gt;"
        )

    def test_highlight_service_summary_limited_if_no_matches(self):

        # 120 words, 600 characters
        really_long_service_summary = "This line has a total of 10 words, 50 characters. " * 12

        service = make_standard_service(
            serviceSummary=really_long_service_summary,
            lot='TaaS'
        )
        # Doesn't actually search by lot, returns all services
        response = self._put_into_and_get_back_from_elasticsearch(
            service=service,
            query_string='lot=TaaS'
        )
        assert_response_status(response, 200)

        search_results = get_json_from_response(response)["documents"]
        # Get the first with a matching value from a list
        search_result = next((s for s in search_results if s['lot'] == 'TaaS'), None)
        assert_true(490 < len(search_result["highlight"]["serviceSummary"][0]) < 510)

    @pytest.mark.parametrize('page_size, multiplier, expected_count',
                             (
                                 ('1', '5', 5),
                                 ('2', '2', 4),
                                 ('1', '10', 10)
                             ))
    def test_id_only_request_has_multiplied_page_size(self, page_size, multiplier, expected_count):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = page_size
            self.app.config['DM_ID_ONLY_SEARCH_PAGE_SIZE_MULTIPLIER'] = multiplier

            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&idOnly=True')
            response_json = get_json_from_response(response)

            assert_response_status(response, 200)
            assert_equal(len(response_json['documents']), expected_count)

    def test_only_ids_returned_for_id_only_request(self):
        with self.app.app_context():
            response = self.client.get(
                '/index-to-create/services/search?q=serviceName&idOnly=True')
            response_json = get_json_from_response(response)

            assert_response_status(response, 200)
            assert_equal(set(response_json['documents'][0].keys()), {'id'})


class TestFetchById(BaseApplicationTestWithIndex):
    def test_should_return_404_if_no_service(self):
        response = self.client.get(
            '/index-to-create/services/100')

        assert_response_status(response, 404)

    def test_should_return_service_by_id(self, default_service):
        service = default_service
        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')

        response = self.client.get(make_search_api_url(service))

        data = get_json_from_response(response)
        assert_response_status(response, 200)

        original_service_id = service.get('document', service.get('service'))['id']  # TODO remove compat shim
        assert data['services']["_id"] == str(original_service_id)
        assert data['services']["_source"]["dmtext_id"] == str(original_service_id)

        cases = (
            "lot",
            "serviceName",
            "serviceSummary",
            "serviceBenefits",
            "serviceFeatures",
            "serviceTypes",
            "supplierName",
        )

        # filter fields are processed (lowercase etc)
        # and also have a new key (filter_FIELDNAME)
        for key in cases:
            original = service.get('document', service.get('service'))[key]  # TODO remove compat shim
            indexed = data['services']["_source"]["dmtext_" + key]
            assert_equal(original, indexed)

    def test_service_should_have_all_exact_match_fields(self, default_service):
        service = default_service
        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('index-to-create')
        response = self.client.get(make_search_api_url(service))

        data = get_json_from_response(response)
        assert_response_status(response, 200)

        cases = [
            "lot",
            "serviceTypes",
            "minimumContractPeriod",
            "networksConnected",
        ]

        for key in cases:
            assert_equal(
                data['services']["_source"]["dmfilter_" + key],
                service.get('document', service.get('service'))[key])  # TODO remove shim


class TestSearchType(BaseApplicationTestWithIndex):
    def test_core_search_and_aggregate_does_dfs_query_for_searches(self):
        with self.app.app_context(), mock.patch.object(es, 'search') as es_search_mock:
            core_search_and_aggregate('index-to-create', 'services', MultiDict(), search=True)

        assert es_search_mock.call_args[1]['search_type'] == 'dfs_query_then_fetch'

    def test_core_search_and_aggregate_does_size_0_query_for_aggregations(self):
        with self.app.app_context(), mock.patch.object(es, 'search') as es_search_mock:
            core_search_and_aggregate('index-to-create', 'services', MultiDict(), aggregations=['serviceCategories'])

        assert es_search_mock.call_args[1]['body']['size'] == 0


class TestSearchResultsOrdering(BaseApplicationTestWithIndex):
    def setup(self):
        super(TestSearchResultsOrdering, self).setup()
        with self.app.app_context():
            services = create_services(10)
            for service in services:
                self.client.put(
                    make_search_api_url(service),
                    data=json.dumps(service),
                    content_type='application/json')
            search_service.refresh('index-to-create')

    def test_should_order_services_by_service_id_sha256(self):
        with self.app.app_context():
            response = self.client.get('/index-to-create/services/search')
            assert_response_status(response, 200)
            assert_equal(get_json_from_response(response)["meta"]["total"], 10)

        ordered_service_ids = [service['id'] for service in json.loads(response.get_data(as_text=True))['documents']]
        assert ordered_service_ids == ['5', '6', '2', '7', '1', '0', '3', '4', '8', '9']  # fixture for sha256 ordering


def create_services(number_of_services):
    services = []
    for i in range(number_of_services):
        service = make_standard_service(id=str(i))
        services.append(service)

    return services
