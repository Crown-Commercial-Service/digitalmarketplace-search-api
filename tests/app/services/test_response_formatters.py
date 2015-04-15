from nose.tools import assert_equal
import json

from app.main.services.response_formatters import \
    convert_es_status, convert_es_results

with open("example_es_responses/status.json") as services:
    STATUS_JSON = json.load(services)

with open("example_es_responses/search_results.json") as search_results:
    SEARCH_RESULTS_JSON = json.load(search_results)


def test_should_build_query_block_in_response():
    res = convert_es_results(SEARCH_RESULTS_JSON,
                             {"q": "keywords", "category": "some catergory"})
    assert_equal(res["query"]["q"], "keywords")
    assert_equal(res["query"]["category"], "some catergory")


def test_should_build_search_response_from_es_response():
    res = convert_es_results(SEARCH_RESULTS_JSON, {"q": "keywords"})
    assert_equal(res["query"]["q"], "keywords")
    assert_equal(res["total"], 628)
    assert_equal(res["took"], 69)
    assert_equal(len(res["services"]), 10)

    assert_equal(res["services"][0]["id"], "5390159512076288")
    assert_equal(res["services"][0]["lot"], "SaaS")
    assert_equal(res["services"][0]["supplierName"], "Supplier Name")
    assert_equal(res["services"][0]["serviceName"], "Email Verification")
    assert_equal(res["services"][0]["serviceTypes"], [
        "Data management"
    ])


def test_should_build_highlights_es_response():
    res = convert_es_results(SEARCH_RESULTS_JSON, {"q": "keywords"})
    assert_equal(
        res["services"][0]["highlight"]["serviceName"],
        ["Email Verification"])
    assert_equal(res["services"][0]["highlight"]["serviceFeatures"], [
        "Verify email addresses at the point of entry",
        "Validate email address format",
        "Live email account",
        "Safe to email"
    ])
    assert_equal(res["services"][0]["highlight"]["serviceBenefits"], [
        "Increase email deliverability"
    ])


def test_should_not_include_highlights_if_not_in_es_results():
    copy = SEARCH_RESULTS_JSON
    del copy["hits"]["hits"][0]["highlight"]
    res = convert_es_results(copy, {"category": "some catergory"})
    assert_equal("highlight" in res["services"][0], False)


def test_should_build_status_response_from_es_response():
    res = convert_es_status(STATUS_JSON, "g-cloud")
    assert_equal(res["num_docs"], 10380)
    assert_equal(res["primary_size"], "16.8mb")


def test_should_build_status_response_from_es_response_with_empty_index():
    status_json_with_no_docs = dict(STATUS_JSON)
    del status_json_with_no_docs["indices"]["g-cloud"]["docs"]
    res = convert_es_status(status_json_with_no_docs, "g-cloud")
    assert_equal("num_docs" in res, False)
    assert_equal(res["primary_size"], "16.8mb")
