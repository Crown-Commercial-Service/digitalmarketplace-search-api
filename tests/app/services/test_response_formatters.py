import mock
from flask import json

from app.main.services.response_formatters import \
    convert_es_status, convert_es_results


with open("example_es_responses/stats.json") as services:
    STATS_JSON = json.load(services)

with open("example_es_responses/services_index_info.json") as services:
    SERVICES_INDEX_INFO_JSON = json.load(services)

with open("example_es_responses/briefs_index_info.json") as briefs:
    BRIEFS_INDEX_INFO_JSON = json.load(briefs)

with open("example_es_responses/search_results.json") as search_results:
    SEARCH_RESULTS_JSON = json.load(search_results)


@mock.patch('app.main.services.response_formatters.current_app')
def test_should_build_query_block_in_response(current_app, services_mapping):
    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON,
                             {"q": "keywords", "category": "some catergory"})
    assert res["meta"]["query"]["q"] == "keywords"
    assert res["meta"]["query"]["category"] == "some catergory"


@mock.patch('app.main.services.response_formatters.current_app')
def test_should_build_search_response_from_es_response(current_app, services_mapping):
    current_app.config = {'DM_SEARCH_PAGE_SIZE': 30}

    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON, {"q": "keywords"})

    assert res["meta"]["query"]["q"] == "keywords"
    assert res["meta"]["total"] == 10
    assert res["meta"]["took"] == 15
    assert res["meta"]["results_per_page"] == 30
    assert len(res["documents"]) == 10

    assert res["documents"][0]["id"] == "144159043984122"
    assert res["documents"][0]["lot"] == "cloud-support"
    assert res["documents"][0]["frameworkName"] == "G-Cloud 12"
    assert res["documents"][0]["supplierName"] == "Supplier Name"
    assert res["documents"][0]["serviceName"] == "Plant-based cloud hosting"
    assert res["documents"][0]["serviceCategories"] == ["Ongoing support"]


@mock.patch('app.main.services.response_formatters.current_app')
def test_should_build_highlights_es_response(current_app, services_mapping):
    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON, {"q": "keywords"})
    assert res["documents"][0]["highlight"]["serviceName"] == ["Plant-based cloud hosting"]
    assert res["documents"][0]["highlight"]["serviceFeatures"] == [
        "Independent advice and expertise",
    ]
    assert res["documents"][0]["highlight"]["serviceBenefits"] == [
        "Fully scalable and flexible solutions to suit changing needs"
    ]


@mock.patch('app.main.services.response_formatters.current_app')
def test_should_not_include_highlights_if_not_in_es_results(current_app, services_mapping):
    copy = SEARCH_RESULTS_JSON
    del copy["hits"]["hits"][0]["highlight"]
    res = convert_es_results(services_mapping, copy, {"category": "some catergory"})
    assert "highlight" not in res["documents"][0]


def test_should_build_status_response_from_es_response():
    res = convert_es_status("g-cloud-12", STATS_JSON, SERVICES_INDEX_INFO_JSON)
    assert res == {
        "num_docs": 36311,
        "primary_size": "73.7mb",
        "mapping_version": "17.13.1",
        "mapping_generated_from_framework": "g-cloud-12",
        "max_result_window": 50000,
        "aliases": [],
    }


def test_should_build_status_response_from_briefs_es_response():
    res = convert_es_status("briefs-digital-outcomes-and-specialists", STATS_JSON, BRIEFS_INDEX_INFO_JSON)
    assert res == {
        "num_docs": 1192,
        "primary_size": "2mb",
        "mapping_version": "11.0.0",
        "mapping_generated_from_framework": "digital-outcomes-and-specialists-2",
        "max_result_window": 10000,
        "aliases": [],
    }


def test_should_build_status_response_from_es_response_with_empty_index():
    stats_json_with_no_docs = dict(STATS_JSON)
    del stats_json_with_no_docs["indices"]["g-cloud-12"]["primaries"]["docs"]
    res = convert_es_status("g-cloud-12", stats_json_with_no_docs)
    assert res == {
        "aliases": [],
        "mapping_version": None,
        "mapping_generated_from_framework": None,
        "max_result_window": None,
        "num_docs": None,
        "primary_size": "73.7mb",
    }
