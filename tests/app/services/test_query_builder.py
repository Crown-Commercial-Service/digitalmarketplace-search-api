from nose.tools import (
    assert_equal, assert_in, assert_not_in,
    assert_false, assert_true
)
from app.main.services.query_builder import construct_query, is_filtered
from app.main.services.query_builder import (
    field_is_or_filter, field_filters,
    or_field_filters, and_field_filters,
    filter_clause
)
from werkzeug.datastructures import MultiDict


def test_should_have_correct_root_element():
    assert_equal("query" in construct_query(build_query_params()), True)


def test_should_have_page_size_set():
    assert_equal(construct_query(build_query_params())["size"], 100)


def test_should_be_able_to_override_pagesize():
    assert_equal(construct_query(build_query_params(), 10)["size"], 10)


def test_page_should_set_from_parameter():
    assert_equal(
        construct_query(build_query_params(page=2))["from"], 100)


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
    assert_in("simple_query_string", query["query"])
    query_string_clause = query["query"]["simple_query_string"]
    assert_equal(query_string_clause["query"], keywords)
    assert_equal(query_string_clause["default_operator"], "and")
    assert_equal(query_string_clause["fields"], [
        "frameworkName",
        "id",
        "lot",
        "serviceBenefits",
        "serviceFeatures",
        "serviceName",
        "serviceSummary",
        "serviceTypes",
        "supplierName",
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
    )["query"]["filtered"]["query"]
    assert_in("simple_query_string", query)
    query_string_clause = query["simple_query_string"]
    assert_equal(query_string_clause["query"], "some keywords")
    assert_equal(query_string_clause["default_operator"], "and")
    assert_equal(query_string_clause["fields"], [
        "frameworkName",
        "id",
        "lot",
        "serviceBenefits",
        "serviceFeatures",
        "serviceName",
        "serviceSummary",
        "serviceTypes",
        "supplierName",
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


def test_highlight_block_sets_encoder_to_html():
    query = construct_query(
        build_query_params(keywords="some keywords",
                           service_types=["some serviceTypes"]))

    assert_equal(query["highlight"]["encoder"], "html")


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


def build_query_params(keywords=None, service_types=None, lot=None, page=None):
    query_params = MultiDict()
    if keywords:
        query_params["q"] = keywords
    if service_types:
        for service_type in service_types:
            query_params.add("filter_serviceTypes", service_type)
    if lot:
        query_params["filter_lot"] = lot
    if page:
        query_params["page"] = page
    return query_params


class TestFieldFilters(object):
    def test_field_is_or_filter(self):
        assert_true(field_is_or_filter(['a,b']))

    def test_field_is_or_filter_no_comma(self):
        assert_false(field_is_or_filter(['a']))

    def test_field_is_or_filter_multiple_values_no_comma(self):
        assert_false(field_is_or_filter(['a', 'b']))

    def test_field_is_or_filter_multiple_values(self):
        assert_false(field_is_or_filter(['a,b', 'b,c']))

    def test_or_field_filters(self):
        assert_equal(
            or_field_filters('filterName', ['Aa bb', 'Bb cc']),
            [{"terms": {"filterName": ['aabb', 'bbcc'], "execution": "bool"}}]
        )

    def test_or_field_filters_single_value(self):
        assert_equal(
            or_field_filters('filterName', ['Aa bb']),
            [{"terms": {"filterName": ['aabb'], "execution": "bool"}}]
        )

    def test_and_field_filters(self):
        assert_equal(
            and_field_filters('filterName', ['Aa bb', 'Bb cc']),
            [
                {"term": {"filterName": 'aabb'}},
                {"term": {"filterName": 'bbcc'}}
            ]
        )

    def test_and_field_filters_single_value(self):
        assert_equal(
            and_field_filters('filterName', ['Aa bb']),
            [{"term": {"filterName": 'aabb'}}]
        )

    def test_field_filters_single_value(self):
        assert_equal(
            field_filters('filterName', ['Aa Bb']),
            [{"term": {"filterName": 'aabb'}}]
        )

    def test_field_filters_multiple_and_values(self):
        assert_equal(
            field_filters('filterName', ['Aa bb', 'Bb,Cc']),
            [
                {"term": {"filterName": 'aabb'}},
                {"term": {"filterName": 'bbcc'}}
            ]
        )

    def test_field_filters_or_value(self):
        assert_equal(
            field_filters('filterName', ['Aa,Bb']),
            [{"terms": {"filterName": ['aa', 'bb'], "execution": "bool"}}]
        )


class TestFilterClause(object):
    def test_filter_ignores_non_filter_query_args(self):
        assert_equal(
            filter_clause(
                MultiDict({'fieldName': ['Aa bb'], 'lot': ['saas']})
            ),
            {'bool': {'must': []}}
        )

    def test_single_and_field(self):
        assert_equal(
            filter_clause(MultiDict(
                {'filter_fieldName': ['Aa bb'], 'lot': 'saas'}
            )),
            {'bool': {
                'must': [
                    {"term": {"filter_fieldName": 'aabb'}},
                ]
            }}
        )

    def test_single_or_field(self):
        assert_equal(
            filter_clause(MultiDict({'filter_fieldName': ['Aa,Bb']})),
            {'bool': {
                'must': [
                    {"terms": {"filter_fieldName": ['aa', 'bb'], "execution": "bool"}},
                ]
            }}
        )

    def test_or_and_combination(self):
        bool_filter = filter_clause(MultiDict({
            'filter_andFieldName': ['Aa', 'bb'],
            'filter_orFieldName': ['Aa,Bb']
        }))

        assert_in(
            {"terms": {"filter_orFieldName": ['aa', 'bb'], "execution": "bool"}},
            bool_filter['bool']['must']
        )

        assert_in(
            {"term": {"filter_andFieldName": 'aa'}},
            bool_filter['bool']['must']
        )

        assert_in(
            {"term": {"filter_andFieldName": 'bb'}},
            bool_filter['bool']['must']
        )
