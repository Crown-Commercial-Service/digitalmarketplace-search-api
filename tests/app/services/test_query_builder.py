from nose.tools import assert_equal, assert_in, assert_false
from app.main.services.query_builder import construct_query, \
    is_filtered, extract_service_types


def test_should_have_correct_root_element():
    assert_equal("query" in construct_query(build_query_params()), True)


def test_should_have_page_size_set():
    assert_equal(construct_query(build_query_params())["size"], 100)


def test_should_be_able_to_override_pagesize():
    assert_equal(construct_query(build_query_params(), 10)["size"], 10)


def test_should_have_from_set():
    assert_equal(construct_query(build_query_params(from_param=100))["from"], 100)


def test_should_have_no_from_by_default():
    assert_false("from" in construct_query(build_query_params()))


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
        "supplierName"
    ]
                 )


def test_should_identify_filter_search_from_query_params():
    assert_equal(is_filtered(build_query_params()), False)
    assert_equal(is_filtered(build_query_params(lot="lot")), True)
    assert_equal(
        is_filtered(build_query_params(service_types="serviceTypes")), True)


def test_should_have_filtered_root_element_if_service_types_search():
    query = construct_query(build_query_params(
        service_types="my serviceTypes"))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_if_lot_search():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_and_match_all_if_no_keywords():
    query = construct_query(build_query_params(
        service_types="my serviceTypes"))
    assert_equal("match_all" in query["query"]["filtered"]["query"], True)


def test_should_have_filtered_root_element_and_match_keywords():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types="my serviceTypes")
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
        "supplierName"
    ]
                 )


def test_should_have_filtered_term_service_types_clause():
    query = construct_query(build_query_params(service_types="serviceTypes"))
    assert_equal("term" in
                 query["query"]["filtered"]["filter"]["bool"]["must"][0], True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["serviceTypesExact"],
        "servicetypes")


def test_should_have_filtered_term_lot_clause():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]["bool"]["must"][0]["term"]["lot"],
        "SaaS")


def test_should_have_filtered_term_for_lot_and_service_types_clause():
    query = construct_query(
        build_query_params(lot="SaaS", service_types="serviceTypes"))
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'serviceTypesExact': 'servicetypes'}}, terms)
    assert_in({"term": {'lot': 'SaaS'}}, terms)


def test_should_build_trimmed_list_from_service_types():
    st = "this is a service, and so is this,one more for the road"
    service_types = extract_service_types(
        build_query_params(service_types=st))
    assert_equal("this is a service" in service_types, True)
    assert_equal("and so is this" in service_types, True)
    assert_equal("one more for the road" in service_types, True)


def test_should_have_filtered_term_for_multiple_service_types_clauses():
    query = construct_query(
        build_query_params(
            service_types="serviceTypes1,serviceTypes2,serviceTypes3"))
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'serviceTypesExact': 'servicetypes1'}}, terms)
    assert_in({"term": {'serviceTypesExact': 'servicetypes2'}}, terms)
    assert_in({"term": {'serviceTypesExact': 'servicetypes3'}}, terms)


def test_should_use_whitespace_stripped_lowercased_service_types():
    query = construct_query(build_query_params(
        service_types="My serviceTypes"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["serviceTypesExact"],
        "myservicetypes")


def test_should_use_no_non_alphanumeric_characters_in_service_types():
    query = construct_query(
        build_query_params(service_types="Mys Service TYPes"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]["bool"]["must"][0]
        ["term"]["serviceTypesExact"],
        "mysservicetypes")


def test_should_have_highlight_block_on_keyword_search():
    query = construct_query(build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)


def test_should_have_highlight_block_on_filtered_search():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types="some serviceTypes"))

    assert_equal("highlight" in query, True)


def test_highlight_block_contains_correct_fields():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types="some serviceTypes"))

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


# TODO convert to ImmutableDict
def build_query_params(
        keywords=None,
        service_types=None,
        lot=None,
        from_param=None):
    query_params = {}
    if keywords:
        query_params["q"] = keywords
    if service_types:
        query_params["serviceTypes"] = service_types
    if lot:
        query_params["lot"] = lot
    if from_param:
        query_params["from"] = from_param
    return query_params
