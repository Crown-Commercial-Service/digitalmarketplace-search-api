import types
from nose.tools import assert_equal, assert_in, assert_not_in
from app.main.services.query_builder import construct_query, \
    is_filtered
from werkzeug.datastructures import MultiDict


def test_should_have_correct_root_element():
    assert_equal("query" in construct_query(build_query_params()), True)


def test_should_have_match_all_query_if_no_params():
    assert_equal("query" in construct_query(build_query_params()), True)
    assert_equal("match_all" in
                 construct_query(build_query_params())["query"], True)


def test_should_make_multi_match_query_if_keywords_supplied():
    keywords = "these are my keywords"
    query = construct_query(build_query_params(keywords))
    assert_equal("query" in query, True)
    assert_equal("multi_match" in query["query"], True)
    multi_match_clause = query["query"]["multi_match"]
    assert_equal(multi_match_clause["query"], keywords)
    assert_equal(multi_match_clause["operator"], "and")
    assert_equal(multi_match_clause["fields"], [
        "id",
        "lot",
        "serviceName",
        "serviceSummary",
        "serviceFeatures",
        "serviceBenefits",
        "serviceTypes",
        "supplierName",
        "frameworkName"
    ])


def test_should_identify_filter_search_from_query_params():
    cases = (
        (build_query_params(), False),
        (build_query_params(keywords="lot"), False),
        (build_query_params(lot="lot"), True),
        (build_query_params(keywords="something", lot="lot"), True),
        (build_query_params(service_types=["serviceTypes"]), True)
    )

    for query, expected in cases:
        yield assert_equal, is_filtered(query), expected


def test_should_have_filtered_root_element_if_service_types_search():
    query = construct_query(build_query_params(
        service_types=["my serviceTypes"]))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_if_lot_search():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_and_match_all_if_no_keywords():
    query = construct_query(build_query_params(
        service_types=["my serviceTypes"]))
    assert_equal("match_all" in query["query"]["filtered"]["query"], True)


def test_should_have_filtered_root_element_and_match_keywords():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types=["my serviceTypes"])
    )
    assert_equal("multi_match" in query["query"]["filtered"]["query"], True)
    multi_match_clause = query["query"]["filtered"]["query"]["multi_match"]
    assert_equal(multi_match_clause["query"], "some keywords")
    assert_equal(multi_match_clause["operator"], "and")
    assert_equal(multi_match_clause["fields"], [
        "id",
        "lot",
        "serviceName",
        "serviceSummary",
        "serviceFeatures",
        "serviceBenefits",
        "serviceTypes",
        "supplierName",
        "frameworkName"
    ])


def test_should_have_filtered_term_service_types_clause():
    query = construct_query(build_query_params(service_types=["serviceTypes"]))
    assert_equal("term" in
                 query["query"]["filtered"]["filter"]["bool"]["must"][0], True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["filter_serviceTypes"],
        "servicetypes")


def test_should_have_filtered_term_lot_clause():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["filter_lot"],
        "saas")


def test_should_have_filtered_term_for_lot_and_service_types_clause():
    query = construct_query(
        build_query_params(lot="SaaS", service_types=["serviceTypes"]))
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'filter_serviceTypes': 'servicetypes'}}, terms)
    assert_in({"term": {'filter_lot': 'saas'}}, terms)


def test_should_not_filter_on_unknown_keys():
    params = build_query_params(lot="SaaS", service_types=["serviceTypes"])
    params.add("this", "that")
    query = construct_query(params)
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'filter_serviceTypes': 'servicetypes'}}, terms)
    assert_in({"term": {'filter_lot': 'saas'}}, terms)
    assert_not_in({"term": {'unknown': 'something to ignore'}}, terms)


def test_should_have_filtered_term_for_multiple_service_types_clauses():
    query = construct_query(
        build_query_params(
            service_types=["serviceTypes1", "serviceTypes2", "serviceTypes3"]))
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'filter_serviceTypes': 'servicetypes1'}}, terms)
    assert_in({"term": {'filter_serviceTypes': 'servicetypes2'}}, terms)
    assert_in({"term": {'filter_serviceTypes': 'servicetypes3'}}, terms)


def test_should_use_whitespace_stripped_lowercased_service_types():
    query = construct_query(build_query_params(
        service_types=["My serviceTypes"]))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["filter_serviceTypes"],
        "myservicetypes")


def test_should_use_no_non_alphanumeric_characters_in_service_types():
    query = construct_query(
        build_query_params(service_types=["Mys Service TYPes"]))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]["bool"]["must"][0]
        ["term"]["filter_serviceTypes"],
        "mysservicetypes")


def test_should_have_highlight_block_on_keyword_search():
    query = construct_query(build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)


def test_should_have_highlight_block_on_filtered_search():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types=["some serviceTypes"]))

    assert_equal("highlight" in query, True)


def test_highlight_block_contains_correct_fields():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types=["some serviceTypes"]))

    assert_equal("highlight" in query, True)

    cases = [
        ("id", True),
        ("lot", True),
        ("serviceName", True),
        ("serviceSummary", True),
        ("serviceFeatures", True),
        ("serviceBenefits", True),
        ("serviceTypes", True),
        ("supplierName", True)
    ]

    for example, expected in cases:
        yield \
            assert_equal, \
            example in query["highlight"]["fields"], \
            expected, \
            example


def build_query_params(keywords=None, service_types=None, lot=None):
    query_params = MultiDict()
    if keywords:
        query_params["q"] = keywords
    if service_types:
        for service_type in service_types:
            query_params.add("filter_serviceTypes", service_type)
    if lot:
        query_params["filter_lot"] = lot

    return query_params
