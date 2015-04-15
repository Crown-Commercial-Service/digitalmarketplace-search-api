from nose.tools import assert_equal, assert_in
from app.main.services.query_builder import construct_query, is_filtered


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
        "supplierName"
    ]
    )


def test_should_identify_filter_search_from_query_params():
    assert_equal(is_filtered(build_query_params()), False)
    assert_equal(is_filtered(build_query_params(lot="lot")), True)
    assert_equal(is_filtered(build_query_params(category="category")), True)


def test_should_have_filtered_root_element_if_category_search():
    query = construct_query(build_query_params(category="my category"))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_if_lot_search():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal("query" in query, True)
    assert_equal("filtered" in query["query"], True)


def test_should_have_filtered_root_element_and_match_all_if_no_keywords():
    query = construct_query(build_query_params(category="my category"))
    assert_equal("match_all" in query["query"]["filtered"]["query"], True)


def test_should_have_filtered_root_element_and_match_keywords():
    query = construct_query(
        build_query_params(keywords="some keywords", category="my category"))
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


def test_should_have_filtered_term_category_clause():
    query = construct_query(build_query_params(category="category"))
    assert_equal("term" in
                 query["query"]["filtered"]["filter"]["bool"]["must"][0], True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["serviceTypesExact"],
        "category")


def test_should_have_filtered_term_lot_clause():
    query = construct_query(build_query_params(lot="SaaS"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]["bool"]["must"][0]["term"]["lot"],
        "SaaS")


def test_should_have_filtered_term_for_lot_and_category_clause():
    query = construct_query(
        build_query_params(lot="SaaS", category="category"))
    terms = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert_in({"term": {'serviceTypesExact': 'category'}}, terms)
    assert_in({"term": {'lot': 'SaaS'}}, terms)


def test_should_use_whitespace_stripped_lowercased_category():
    query = construct_query(build_query_params(category="My Category"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]
        ["bool"]["must"][0]["term"]["serviceTypesExact"],
        "mycategory")


def test_should_use_no_non_alphanumeric_characters_in_category():
    query = construct_query(build_query_params(category="My's Cate:gory"))
    assert_equal(
        "term" in query["query"]["filtered"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["filtered"]["filter"]["bool"]["must"][0]
        ["term"]["serviceTypesExact"],
        "myscategory")


def test_should_have_highlight_block_on_keyword_search():
    query = construct_query(build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)


def test_should_have_highlight_block_on_filtered_search():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           category="some category"))

    assert_equal("highlight" in query, True)


def test_highlight_block_contains_correct_fields():
    query = construct_query(
        build_query_params(keywords="some keywords", category="some category"))

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
def build_query_params(keywords=None, category=None, lot=None):
    query_params = {}
    if keywords:
        query_params["q"] = keywords
    if category:
        query_params["category"] = category
    if lot:
        query_params["lot"] = lot

    return query_params
