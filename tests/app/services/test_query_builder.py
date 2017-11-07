from nose.tools import (
    assert_equal, assert_in, assert_not_in,
    assert_false, assert_true
)
import pytest
import app.mapping
from app.main.services.query_builder import construct_query, is_filtered
from app.main.services.query_builder import (
    field_is_or_filter,
    field_filters,
    filter_clause,
)
from werkzeug.datastructures import MultiDict
from tests.app.helpers import build_query_params


pytestmark = pytest.mark.usefixtures("services_mapping")


def test_should_have_correct_root_element(services_mapping):
    assert_equal("query" in construct_query(services_mapping, build_query_params()), True)


def test_should_have_page_size_set(services_mapping):
    assert_equal(construct_query(services_mapping, build_query_params())["size"], 100)


def test_should_be_able_to_override_pagesize(services_mapping):
    assert_equal(construct_query(services_mapping, build_query_params(), page_size=10)["size"], 10)


def test_page_should_set_from_parameter(services_mapping):
    assert_equal(
        construct_query(services_mapping, build_query_params(page=2))["from"], 100)


def test_should_have_no_from_by_default(services_mapping):
    assert_false("from" in construct_query(services_mapping, build_query_params()))


def test_should_have_match_all_query_if_no_params(services_mapping):
    assert_equal("query" in construct_query(services_mapping, build_query_params()), True)
    assert_equal("match_all" in
                 construct_query(services_mapping, build_query_params())["query"], True)


@pytest.mark.parametrize('aggregations, equality', (([], False), (['lot'], True)))
def test_aggregations_root_element_present_if_appropriate(services_mapping, aggregations, equality):
    assert_equal('aggregations' in construct_query(services_mapping, build_query_params(), aggregations=aggregations),
                 equality)
    assert_equal('aggregations' in construct_query(services_mapping, build_query_params(), aggregations=aggregations),
                 equality)


@pytest.mark.parametrize('aggregations', ((['lot']), (['lot', 'serviceCategories'])))
def test_aggregations_terms_added_for_each_param(services_mapping, aggregations):
    query = construct_query(services_mapping, build_query_params(), aggregations=aggregations)

    assert_equal(set(aggregations), {x for x in query['aggregations']})
    assert {"_".join(("dmagg", x)) for x in aggregations} == {
        v['terms']['field'] for k, v in query['aggregations'].items()
    }


def test_aggregation_throws_error_if_not_implemented(services_mapping):
    with pytest.raises(ValueError):
        construct_query(services_mapping, build_query_params(), aggregations=['missing'])


def test_should_make_multi_match_query_if_keywords_supplied(services_mapping):
    keywords = "these are my keywords"
    query = construct_query(services_mapping, build_query_params(keywords))
    assert_equal("query" in query, True)
    assert_in("simple_query_string", query["query"])
    query_string_clause = query["query"]["simple_query_string"]
    assert_equal(query_string_clause["query"], keywords)
    assert_equal(query_string_clause["default_operator"], "and")
    assert frozenset(query_string_clause["fields"]) == frozenset(
        "_".join(("dmtext", f)) for f in services_mapping.fields_by_prefix["dmtext"]
    )


@pytest.mark.parametrize("query,expected", (
    (build_query_params(), False),
    (build_query_params(keywords="lot"), False),
    (build_query_params(filters={'lot': "lot"}), True),
    (build_query_params(keywords="something", filters={'lot': "lot"}), True),
    (build_query_params(filters={'serviceTypes': ["serviceTypes"]}), True)
))
def test_should_identify_filter_search_from_query_params(services_mapping, query, expected):
    return assert_equal, is_filtered(services_mapping, query), expected, query


def test_should_have_filtered_root_element_if_service_types_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'serviceTypes': ["serviceTypes"]}))
    assert_equal("query" in query, True)
    assert_equal("bool" in query["query"], True)
    assert_equal("must" in query["query"]["bool"], True)


def test_should_have_filtered_root_element_if_lot_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'lot': "SaaS"}))
    assert_equal("query" in query, True)
    assert_equal("bool" in query["query"], True)
    assert_equal("must" in query["query"]["bool"], True)


def test_should_have_filtered_root_element_and_match_all_if_no_keywords(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'serviceTypes': ["my serviceTypes"]}))
    assert_equal("match_all" in query["query"]["bool"]["must"], True)


def test_should_have_filtered_root_element_and_match_keywords(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords",
                                                                 filters={'serviceTypes': ["my serviceTypes"]})
                            )["query"]["bool"]["must"]
    assert_in("simple_query_string", query)
    query_string_clause = query["simple_query_string"]
    assert_equal(query_string_clause["query"], "some keywords")
    assert_equal(query_string_clause["default_operator"], "and")
    assert frozenset(query_string_clause["fields"]) == frozenset(
        "_".join(("dmtext", f)) for f in services_mapping.fields_by_prefix["dmtext"]
    )


def test_should_have_filtered_term_service_types_clause(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'serviceTypes': ["serviceTypes"]}))
    assert_equal("term" in
                 query["query"]["bool"]["filter"]["bool"]["must"][0], True)
    assert_equal(
        query["query"]["bool"]["filter"]
        ["bool"]["must"][0]["term"]["dmfilter_serviceTypes"],
        "serviceTypes")


def test_should_have_filtered_term_lot_clause(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'lot': "SaaS"}))
    assert_equal(
        "term" in query["query"]["bool"]["filter"]["bool"]["must"][0],
        True)
    assert_equal(
        query["query"]["bool"]["filter"]
        ["bool"]["must"][0]["term"]["dmfilter_lot"],
        "SaaS")


def test_should_have_filtered_term_for_lot_and_service_types_clause(services_mapping):
    query = construct_query(services_mapping,
                            build_query_params(filters={'lot': "SaaS", 'serviceTypes': ["serviceTypes"]}))
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert_in({"term": {'dmfilter_serviceTypes': 'serviceTypes'}}, terms)
    assert_in({"term": {'dmfilter_lot': 'SaaS'}}, terms)


def test_should_not_filter_on_unknown_keys(services_mapping):
    params = build_query_params(filters={'lot': "SaaS", 'serviceTypes': ["serviceTypes"]})
    params.add("this", "that")
    query = construct_query(services_mapping, params)
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert_in({"term": {'dmfilter_serviceTypes': 'serviceTypes'}}, terms)
    assert_in({"term": {'dmfilter_lot': 'SaaS'}}, terms)
    assert_not_in({"term": {'unknown': 'something to ignore'}}, terms)


def test_should_have_filtered_term_for_multiple_service_types_clauses(services_mapping):
    query = construct_query(services_mapping,
                            build_query_params(filters={
                                'serviceTypes': ["serviceTypes1", "serviceTypes2", "serviceTypes3"]}))
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert_in({"term": {'dmfilter_serviceTypes': 'serviceTypes1'}}, terms)
    assert_in({"term": {'dmfilter_serviceTypes': 'serviceTypes2'}}, terms)
    assert_in({"term": {'dmfilter_serviceTypes': 'serviceTypes3'}}, terms)


def test_should_have_highlight_block_on_keyword_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)


def test_should_have_highlight_block_on_filtered_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)


def test_highlight_block_sets_encoder_to_html(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert_equal(query["highlight"]["encoder"], "html")


def test_service_id_hash_not_in_searched_fields(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert app.mapping.SERVICE_ID_HASH_FIELD_NAME not in query['query']['simple_query_string']['fields']

    query = construct_query(services_mapping, build_query_params(filters={'serviceTypes': ["serviceType1"]}))

    assert app.mapping.SERVICE_ID_HASH_FIELD_NAME not in query['highlight']['fields']


def test_sort_results_by_score_and_service_id_hash(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))
    assert query['sort'] == ['_score', {"dmsortonly_serviceIdHash": 'desc'}]


@pytest.mark.parametrize('example, expected', (
    ("id", True),
    ("lot", True),
    ("serviceName", True),
    ("serviceSummary", True),
    ("serviceFeatures", True),
    ("serviceBenefits", True),
    ("serviceTypes", True),
    ("supplierName", True)
))
def test_highlight_block_contains_correct_fields(services_mapping, example, expected):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert_equal("highlight" in query, True)

    assert_equal, \
        example in query["highlight"]["fields"], \
        expected, \
        example


class TestFieldFilters(object):
    def test_field_is_or_filter(self):
        assert_true(field_is_or_filter(['a,b']))

    def test_field_is_or_filter_no_comma(self):
        assert_false(field_is_or_filter(['a']))

    def test_field_is_or_filter_multiple_values_no_comma(self):
        assert_false(field_is_or_filter(['a', 'b']))

    def test_field_is_or_filter_multiple_values(self):
        assert_false(field_is_or_filter(['a,b', 'b,c']))

    def test_or_field_filters(self, services_mapping):
        assert_equal(
            field_filters(services_mapping, 'filterName', ['Aa bb,Bb cc']),
            [{"terms": {"dmfilter_filterName": ['Aa bb', 'Bb cc']}}]
        )

    def test_and_field_filters(self, services_mapping):
        assert_equal(
            field_filters(services_mapping, 'filterName', ['Aa bb', 'Bb cc']),
            [
                {"term": {"dmfilter_filterName": 'Aa bb'}},
                {"term": {"dmfilter_filterName": 'Bb cc'}}
            ]
        )

    def test_field_filters_single_value(self, services_mapping):
        assert_equal(
            field_filters(services_mapping, 'filterName', ['Aa Bb']),
            [{"term": {"dmfilter_filterName": 'Aa Bb'}}]
        )

    def test_field_filters_multiple_and_values(self, services_mapping):
        assert_equal(
            field_filters(services_mapping, 'filterName', ['Aa bb', 'Bb,Cc']),
            [
                {"term": {"dmfilter_filterName": 'Aa bb'}},
                {"term": {"dmfilter_filterName": 'Bb,Cc'}}
            ]
        )

    def test_field_filters_or_value(self, services_mapping):
        assert_equal(
            field_filters(services_mapping, 'filterName', ['Aa,Bb']),
            [{"terms": {"dmfilter_filterName": ['Aa', 'Bb']}}]
        )


class TestFilterClause(object):
    def test_filter_ignores_non_filter_query_args(self, services_mapping):
        assert_equal(
            filter_clause(
                services_mapping,
                MultiDict({'fieldName': ['Aa bb'], 'lot': ['saas']}),
            ),
            {'bool': {'must': []}}
        )

    def test_single_and_field(self, services_mapping):
        assert_equal(
            filter_clause(
                services_mapping,
                MultiDict({'filter_fieldName': ['Aa bb'], 'lot': 'saas'}),
            ),
            {'bool': {
                'must': [
                    {"term": {"dmfilter_fieldName": 'Aa bb'}},
                ]
            }}
        )

    def test_single_or_field(self, services_mapping):
        assert_equal(
            filter_clause(services_mapping, MultiDict({'filter_fieldName': ['Aa,Bb']})),
            {'bool': {
                'must': [
                    {"terms": {"dmfilter_fieldName": ['Aa', 'Bb']}},
                ]
            }}
        )

    def test_or_and_combination(self, services_mapping):
        bool_filter = filter_clause(services_mapping, MultiDict({
            'filter_andFieldName': ['Aa', 'bb'],
            'filter_orFieldName': ['Aa,Bb']
        }))

        assert_in(
            {"terms": {"dmfilter_orFieldName": ['Aa', 'Bb']}},
            bool_filter['bool']['must']
        )

        assert_in(
            {"term": {"dmfilter_andFieldName": 'Aa'}},
            bool_filter['bool']['must']
        )

        assert_in(
            {"term": {"dmfilter_andFieldName": 'bb'}},
            bool_filter['bool']['must']
        )
