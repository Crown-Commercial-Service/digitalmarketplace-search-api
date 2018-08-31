from flask import json

import pytest

from app.main.services.response_formatters import \
    convert_es_status, convert_es_results


pytestmark = pytest.mark.usefixtures("services_mapping")


with open("example_es_responses/stats.json") as services:
    STATS_JSON = json.load(services)

with open("example_es_responses/services_index_info.json") as services:
    SERVICES_INDEX_INFO_JSON = json.load(services)

with open("example_es_responses/briefs_index_info.json") as briefs:
    BRIEFS_INDEX_INFO_JSON = json.load(briefs)

with open("example_es_responses/search_results.json") as search_results:
    SEARCH_RESULTS_JSON = json.load(search_results)


def test_should_build_query_block_in_response(services_mapping):
    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON,
                             {"q": "keywords", "category": "some catergory"})
    assert res["meta"]["query"]["q"] == "keywords"
    assert res["meta"]["query"]["category"] == "some catergory"


def test_should_build_search_response_from_es_response(services_mapping):
    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON, {"q": "keywords"})
    assert res["meta"]["query"]["q"] == "keywords"
    assert res["meta"]["total"] == 628
    assert res["meta"]["took"] == 69
    assert len(res["documents"]) == 10

    assert res["documents"][0]["id"] == "5390159512076288"
    assert res["documents"][0]["lot"] == "SaaS"
    assert res["documents"][0]["frameworkName"] == "G-Cloud 6"
    assert res["documents"][0]["supplierName"] == "Supplier Name"
    assert res["documents"][0]["serviceName"] == "Email Verification"
    assert res["documents"][0]["serviceTypes"] == ["Data management"]


def test_should_build_highlights_es_response(services_mapping):
    res = convert_es_results(services_mapping, SEARCH_RESULTS_JSON, {"q": "keywords"})
    assert res["documents"][0]["highlight"]["serviceName"] == ["Email Verification"]
    assert res["documents"][0]["highlight"]["serviceFeatures"] == [
        "Verify email addresses at the point of entry",
        "Validate email address format",
        "Live email account",
        "Safe to email"
    ]
    assert res["documents"][0]["highlight"]["serviceBenefits"] == ["Increase email deliverability"]


def test_should_not_include_highlights_if_not_in_es_results(services_mapping):
    copy = SEARCH_RESULTS_JSON
    del copy["hits"]["hits"][0]["highlight"]
    res = convert_es_results(services_mapping, copy, {"category": "some catergory"})
    assert "highlight" not in res["documents"][0]


def test_should_build_status_response_from_es_response():
    res = convert_es_status("g-cloud-9", STATS_JSON, SERVICES_INDEX_INFO_JSON)
    assert res == {
        "num_docs": 19676,
        "primary_size": "52mb",
        "mapping_version": "9.0.0",
        "mapping_generated_from_framework": "g-cloud-9",
        "max_result_window": 20000,
        "aliases": ["galias"],
    }


def test_should_build_status_response_from_briefs_es_response():
    res = convert_es_status("briefs-digital-outcomes-and-specialists", STATS_JSON, BRIEFS_INDEX_INFO_JSON)
    assert res == {
        "num_docs": 1653,
        "primary_size": "52mb",
        "mapping_version": "11.0.0",
        "mapping_generated_from_framework": "digital-outcomes-and-specialists-2",
        "max_result_window": 10000,
        "aliases": ["galias"],
    }


def test_should_build_status_response_from_es_response_with_empty_index():
    stats_json_with_no_docs = dict(STATS_JSON)
    del stats_json_with_no_docs["indices"]["g-cloud-9"]["primaries"]["docs"]
    res = convert_es_status("g-cloud-9", stats_json_with_no_docs)
    assert res == {
        "aliases": [],
        "mapping_version": None,
        "mapping_generated_from_framework": None,
        "max_result_window": None,
        "num_docs": None,
        "primary_size": "52mb",
    }
