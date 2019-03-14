import mock
import pytest
from flask import json
from werkzeug import MultiDict

from app import elasticsearch_client as es
from app.main.services import search_service
from app.main.services.search_service import core_search_and_aggregate
from tests.helpers import (
    BaseApplicationTestWithIndex,
    make_search_api_url,
    make_service
)


class BaseSearchTestWithServices(BaseApplicationTestWithIndex):
    def setup(self):
        super(BaseSearchTestWithServices, self).setup()
        with self.app.app_context():
            services = []
            for i in range(10):
                service = make_service(id=str(i))
                services.append(service)
                response = self.client.put(
                    make_search_api_url(service),
                    data=json.dumps(service),
                    content_type='application/json')
                assert response.status_code == 200
            search_service.refresh('test-index')


class TestSearchEndpoint(BaseSearchTestWithServices):

    def _put_into_and_get_back_from_elasticsearch(self, service, query_string):

        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service), content_type='application/json')

        with self.app.app_context():
            search_service.refresh('test-index')

        return self.client.get(
            '/test-index/services/search?{}'.format(query_string)
        )

    def test_should_return_service_on_id(self, service):
        response = self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json')
        assert response.status_code == 200

    def test_should_return_service_on_keyword_search(self):
        with self.app.app_context():
            response = self.client.get(
                '/test-index/services/search?q=serviceName')
            assert response.status_code == 200
            assert response.json["meta"]["total"] == 10

    def test_keyword_search_via_alias(self):
        with self.app.app_context():
            self.client.put('/{}'.format('index-alias'), data=json.dumps({
                "type": "alias",
                "target": "test-index",
            }), content_type="application/json")
            response = self.client.get(
                '/index-alias/services/search?q=serviceName')
            assert response.status_code == 200
            assert response.json["meta"]["total"] == 10

    def test_should_get_services_up_to_page_size(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'

            response = self.client.get(
                '/test-index/services/search?q=serviceName'
            )
            assert response.status_code == 200

            assert response.json["meta"]["total"] == 10
            assert len(response.json["documents"]) == 5

    def test_should_get_pagination_links(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '3'

            response = self.client.get(
                '/test-index/services/search?q=serviceName&page=2')
            response_json = response.json

            assert response.status_code == 200
            assert "page=1" in response_json['links']['prev']
            assert "page=3" in response_json['links']['next']

    @pytest.mark.parametrize("page_size,page", (
        (5, 3,),
        (6, 3,),
        (6, 4,),
        (10, 2,),
        (15, 2,),
        (15, 20,),
        # the following are massively out of bounds pages that should be comfortably beyond our ES max_result_window yet
        # should display the same behaviour
        (5, 1000000,),
        (20, 10000000,),
    ))
    def test_should_get_404_on_out_of_bounds_page(self, page_size, page):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = str(page_size)
            response = self.client.get(
                '/test-index/services/search?q=serviceName&page={}'.format(page)
            )
            assert response.status_code == 404

    def test_should_get_400_response__on_negative_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/test-index/services/search?q=serviceName&page=-1')
            assert response.status_code == 400

    def test_should_get_400_response__on_non_numeric_page(self):
        with self.app.app_context():
            self.app.config['DM_SEARCH_PAGE_SIZE'] = '5'
            response = self.client.get(
                '/test-index/services/search?q=serviceName&page=foo')
            assert response.status_code == 400

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
                '/test-index/services/search?q=serviceName&idOnly=True')
            response_json = response.json

            assert response.status_code == 200
            assert len(response_json['documents']) == expected_count

    def test_only_ids_returned_for_id_only_request(self):
        with self.app.app_context():
            response = self.client.get(
                '/test-index/services/search?q=serviceName&idOnly=True')
            response_json = response.json

            assert response.status_code == 200
            assert set(response_json['documents'][0].keys()) == {'id'}


class TestFetchById(BaseApplicationTestWithIndex):
    def test_should_return_404_if_no_service(self):
        response = self.client.get(
            '/test-index/services/100')

        assert response.status_code == 404

    def test_should_return_service_by_id(self, service):
        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('test-index')

        response = self.client.get(make_search_api_url(service))

        data = response.json
        assert response.status_code == 200

        original_service_id = service.get('document', service.get('service'))['id']  # TODO remove compat shim
        assert data['services']["_id"] == str(original_service_id)
        assert data['services']["_source"]["dmtext_id"] == str(original_service_id)

        cases = (
            "lot",
            "serviceName",
            "serviceDescription",
            "serviceBenefits",
            "serviceFeatures",
            "serviceCategories",
            "supplierName",
        )

        # filter fields are processed (lowercase etc)
        # and also have a new key (filter_FIELDNAME)
        for key in cases:
            original = service.get('document', service.get('service'))[key]  # TODO remove compat shim
            indexed = data['services']["_source"]["dmtext_" + key]
            assert original == indexed

    def test_service_should_have_all_exact_match_fields(self, service):
        self.client.put(
            make_search_api_url(service),
            data=json.dumps(service),
            content_type='application/json'
        )

        with self.app.app_context():
            search_service.refresh('test-index')
        response = self.client.get(make_search_api_url(service))

        data = response.json
        assert response.status_code == 200

        cases = [
            "lot",
            "publicSectorNetworksTypes",
            "serviceCategories",
        ]

        for key in cases:
            assert (
                data['services']["_source"]["dmfilter_" + key] ==
                service.get('document', service.get('service'))[key]
            )


class TestSearchType(BaseApplicationTestWithIndex):
    def test_core_search_and_aggregate_does_dfs_query_for_searches(self):
        with self.app.app_context(), mock.patch.object(es, 'search') as es_search_mock:
            core_search_and_aggregate('test-index', 'services', MultiDict(), search=True)

        assert es_search_mock.call_args[1]['search_type'] == 'dfs_query_then_fetch'

    def test_core_search_and_aggregate_does_size_0_query_for_aggregations(self):
        with self.app.app_context(), mock.patch.object(es, 'search') as es_search_mock:
            core_search_and_aggregate('test-index', 'services', MultiDict(), aggregations=['serviceCategories'])

        assert es_search_mock.call_args[1]['body']['size'] == 0


class TestSearchResultsOrdering(BaseSearchTestWithServices):

    def test_should_order_services_by_service_id_sha256(self):
        with self.app.app_context():
            response = self.client.get('/test-index/services/search')
            assert response.status_code == 200
            assert response.json["meta"]["total"] == 10

        ordered_service_ids = [service['id'] for service in json.loads(response.get_data(as_text=True))['documents']]
        assert ordered_service_ids == ['5', '6', '2', '7', '1', '0', '3', '4', '8', '9']  # fixture for sha256 ordering


class TestHighlightedService(BaseApplicationTestWithIndex):

    def setup(self):
        super().setup()

        def put(s):
            response = self.client.put(
                make_search_api_url(s),
                data=json.dumps(s),
                content_type="application/json",
            )
            assert response.status_code == 200
            return response

        with self.app.app_context():
            put(make_service(
                id="1",
                serviceDescription="Accessing, storing and retaining email.",
                lot="cloud-support",
            ))
            put(make_service(
                id="2",
                serviceDescription="The <em>quick</em> brown fox jumped over the <em>lazy</em> dog.",
                lot="mother-goose",
            ))
            put(make_service(
                id="3",
                serviceDescription=(
                    # serviceDescription is limited to 500 characters by validator in
                    # digitalmarketplace-frameworks/frameworks/g-cloud-10/questions/services
                    "This service description has 500 characters. "
                    "It is made of 5 repetitions of a 100 character string.\n"
                    * 5
                ),
                lot="long-text",
            ))

            search_service.refresh("test-index")

    def test_search_results_have_highlighted_service_description(self):
        search_results = self.client.get("/test-index/services/search").json["documents"]
        assert all(doc["highlight"]["serviceDescription"] for doc in search_results)

    def test_highlighted_service_description_has_list_containing_service_description(self):
        search_results = self.client.get("/test-index/services/search").json["documents"]
        cloud_support = [doc for doc in search_results if doc["id"] == "1"][0]["highlight"]["serviceDescription"][0]
        assert (
            cloud_support
            ==
            "Accessing, storing and retaining email."
        )

    @pytest.mark.parametrize(
        "search_query",
        (
            "",
            "?q=long-text",
        )
    )
    def test_highlighted_service_description_always_contains_full_service_description(self, search_query):
        search_results = self.client.get(f"/test-index/services/search{search_query}").json["documents"]
        got = [doc for doc in search_results if doc["id"] == "3"][0]["highlight"]["serviceDescription"][0]
        expected = (
            "This service description has 500 characters. "
            "It is made of 5 repetitions of a 100 character string.\n"
            * 5
        )
        assert 500 == len(got)
        assert expected == got

    def test_search_terms_are_marked_in_highlighted_service_description(self):
        search_results = self.client.get("test-index/services/search?q=storing").json["documents"]
        got = search_results[0]["highlight"]["serviceDescription"][0]
        assert (
            "Accessing, <mark class='search-result-highlighted-text'>storing</mark> and retaining email."
            ==
            got
        )

    def test_highlighted_service_description_can_be_longer_than_500_characters_if_marked(self):
        search_results = self.client.get("/test-index/services/search?q=repetitions").json["documents"]
        got = [doc for doc in search_results if doc["id"] == "3"][0]["highlight"]["serviceDescription"][0]
        expected = (
            "This service description has 500 characters. "
            "It is made of 5 "
            "<mark class='search-result-highlighted-text'>repetitions</mark> "
            "of a 100 character string.\n"
            * 5
        )
        # Some highlighters strip trailing space from the field text
        assert len(got) == len(expected) or len(got) == len(expected) - 1
        assert got == expected or got == expected.strip()

    def test_html_in_highlighted_service_description_is_always_escaped(self):
        search_results = self.client.get("test-index/services/search").json["documents"]
        got = [doc for doc in search_results if doc["id"] == "2"][0]["highlight"]["serviceDescription"][0]
        assert (
            "The &lt;em&gt;quick&lt;&#x2F;em&gt; brown fox "
            "jumped over the &lt;em&gt;lazy&lt;&#x2F;em&gt; dog."
            ==
            got
        )

        search_results = self.client.get("test-index/services/search?q=fox").json["documents"]
        got = search_results[0]["highlight"]["serviceDescription"][0]
        assert (
            "The &lt;em&gt;quick&lt;&#x2F;em&gt; brown "
            "<mark class='search-result-highlighted-text'>fox</mark> "
            "jumped over the &lt;em&gt;lazy&lt;&#x2F;em&gt; dog."
            ==
            got
        )
