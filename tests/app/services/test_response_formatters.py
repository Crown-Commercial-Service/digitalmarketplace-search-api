from nose.tools import assert_equal
import json

from app.main.services.response_formatters import format_status

with open("example_es_responses/status.json") as services:
    STATUS_JSON = json.load(services)


def test_should_build_status_response_from_es_response():
    res = format_status(STATUS_JSON, "g-cloud")
    assert_equal(res["status"]["num_docs"], 10380)
    assert_equal(res["status"]["primary_size"], "16.8mb")


def test_should_build_status_response_from_es_response_with_empty_index():
    status_json_with_no_docs = dict(STATUS_JSON)
    del status_json_with_no_docs["indices"]["g-cloud"]["docs"]
    res = format_status(status_json_with_no_docs, "g-cloud")
    assert_equal("num_docs" in res["status"], False)
    assert_equal(res["status"]["primary_size"], "16.8mb")
