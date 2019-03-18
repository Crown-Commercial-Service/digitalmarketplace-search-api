import pytest
from app.main.services.query_builder import construct_query, is_filtered
from app.main.services.query_builder import (
    field_is_or_filter,
    field_filters,
    filter_clause,
)
from werkzeug.datastructures import MultiDict
from tests.app.helpers import build_query_params


def test_should_have_correct_root_element(services_mapping):
    assert "query" in construct_query(services_mapping, build_query_params())


def test_should_have_page_size_set(services_mapping):
    assert construct_query(services_mapping, build_query_params())["size"] == 100


def test_should_be_able_to_override_pagesize(services_mapping):
    assert construct_query(services_mapping, build_query_params(), page_size=10)["size"] == 10


def test_page_should_set_from_parameter(services_mapping):
    assert construct_query(services_mapping, build_query_params(page=2))["from"] == 100


def test_should_have_no_from_by_default(services_mapping):
    assert "from" not in construct_query(services_mapping, build_query_params())


def test_should_have_match_all_query_if_no_params(services_mapping):
    assert "query" in construct_query(services_mapping, build_query_params())
    assert "match_all" in construct_query(services_mapping, build_query_params())["query"]


def test_aggregations_root_element_present_if_aggregations(services_mapping):
    assert 'aggregations' in construct_query(services_mapping, build_query_params(), aggregations=['lot'])


def test_aggregations_root_element_not_present_if_no_aggregations(services_mapping):
    assert 'aggregations' not in construct_query(services_mapping, build_query_params(), aggregations=[])


@pytest.mark.parametrize('aggregations', ((['lot']), (['lot', 'serviceCategories'])))
def test_aggregations_terms_added_for_each_param(services_mapping, aggregations):
    query = construct_query(services_mapping, build_query_params(), aggregations=aggregations)

    assert set(aggregations) == {x for x in query['aggregations']}
    assert {"_".join(("dmagg", x)) for x in aggregations} == {
        v['terms']['field'] for k, v in query['aggregations'].items()
    }


def test_aggregation_throws_error_if_not_implemented(services_mapping):
    with pytest.raises(ValueError):
        construct_query(services_mapping, build_query_params(), aggregations=['missing'])


def test_should_make_multi_match_query_if_keywords_supplied(services_mapping):
    keywords = "these are my keywords"
    query = construct_query(services_mapping, build_query_params(keywords))
    assert "query" in query
    assert "simple_query_string" in query["query"]
    query_string_clause = query["query"]["simple_query_string"]
    assert query_string_clause["query"] == keywords
    assert query_string_clause["default_operator"] == "and"
    assert frozenset(query_string_clause["fields"]) == frozenset(
        "_".join(("dmtext", f)) for f in services_mapping.fields_by_prefix["dmtext"]
    )


@pytest.mark.parametrize("query,expected", (
    (build_query_params(), False),
    (build_query_params(keywords="lot"), False),
    (build_query_params(filters={'lot': "lot"}), True),
    (build_query_params(keywords="something", filters={'lot': "lot"}), True),
    (build_query_params(filters={'serviceCategories': ["serviceCategories"]}), True)
))
def test_should_identify_filter_search_from_query_params(services_mapping, query, expected):
    assert is_filtered(services_mapping, query) == expected, query


def test_should_have_filtered_root_element_if_service_types_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'serviceCategories': ["serviceCategories"]}))
    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]


def test_should_have_filtered_root_element_if_lot_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'lot': "SaaS"}))
    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]


def test_should_have_filtered_root_element_and_match_all_if_no_keywords(services_mapping):
    query = construct_query(
        services_mapping,
        build_query_params(filters={'serviceCategories': ["my serviceCategories"]})
    )
    assert "match_all" in query["query"]["bool"]["must"]


def test_should_have_filtered_root_element_and_match_keywords(services_mapping):
    query = construct_query(
        services_mapping,
        build_query_params(
            keywords="some keywords",
            filters={'serviceCategories': ["my serviceCategories"]}
        )
    )["query"]["bool"]["must"]

    assert "simple_query_string" in query
    query_string_clause = query["simple_query_string"]
    assert query_string_clause["query"] == "some keywords"
    assert query_string_clause["default_operator"] == "and"
    assert frozenset(query_string_clause["fields"]) == frozenset(
        "_".join(("dmtext", f)) for f in services_mapping.fields_by_prefix["dmtext"]
    )


def test_should_have_filtered_term_service_types_clause(services_mapping):
    query = construct_query(
        services_mapping,
        build_query_params(filters={'serviceCategories': ["serviceCategories"]})
    )
    assert "term" in query["query"]["bool"]["filter"]["bool"]["must"][0]
    assert (
        query["query"]["bool"]["filter"]["bool"]["must"][0]["term"]["dmfilter_serviceCategories"]
        ==
        "serviceCategories"
    )


def test_should_have_filtered_term_lot_clause(services_mapping):
    query = construct_query(services_mapping, build_query_params(filters={'lot': "SaaS"}))
    assert "term" in query["query"]["bool"]["filter"]["bool"]["must"][0]
    assert query["query"]["bool"]["filter"]["bool"]["must"][0]["term"]["dmfilter_lot"] == "SaaS"


def test_should_have_filtered_term_for_lot_and_service_types_clause(services_mapping):
    query = construct_query(services_mapping,
                            build_query_params(filters={'lot': "SaaS", 'serviceCategories': ["serviceCategories"]}))
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert {"term": {'dmfilter_serviceCategories': 'serviceCategories'}} in terms
    assert {"term": {'dmfilter_lot': 'SaaS'}} in terms


def test_should_not_filter_on_unknown_keys(services_mapping):
    params = build_query_params(filters={'lot': "SaaS", 'serviceCategories': ["serviceCategories"]})
    params.add("this", "that")
    query = construct_query(services_mapping, params)
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert {"term": {'dmfilter_serviceCategories': 'serviceCategories'}} in terms
    assert {"term": {'dmfilter_lot': 'SaaS'}} in terms
    assert {"term": {'unknown': 'something to ignore'}} not in terms


def test_should_have_filtered_term_for_multiple_service_types_clauses(services_mapping):
    query = construct_query(
        services_mapping,
        build_query_params(
            filters={
                'serviceCategories': [
                    "serviceCategories1",
                    "serviceCategories2",
                    "serviceCategories3"
                ]
            }
        )
    )
    terms = query["query"]["bool"]["filter"]["bool"]["must"]
    assert {"term": {'dmfilter_serviceCategories': 'serviceCategories1'}} in terms
    assert {"term": {'dmfilter_serviceCategories': 'serviceCategories2'}} in terms
    assert {"term": {'dmfilter_serviceCategories': 'serviceCategories3'}} in terms


def test_should_have_highlight_block_on_keyword_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert "highlight" in query


def test_should_have_highlight_block_on_filtered_search(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert "highlight" in query


def test_highlight_block_sets_encoder_to_html(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert query["highlight"]["encoder"] == "html"


def test_service_id_hash_not_in_searched_fields(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert not any("serviceIdHash" in key for key in query['query']['simple_query_string']['fields'])

    query = construct_query(services_mapping, build_query_params(filters={'serviceCategories': ["serviceType1"]}))

    assert not any("serviceIdHash" in key for key in query['highlight']['fields'])


def test_sort_results_by_score_and_service_id_hash(services_mapping):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))
    assert query['sort'] == ['_score', {"sortonly_serviceIdHash": 'desc'}]


@pytest.mark.parametrize('example', (
    'id',
    'lot',
    'serviceName',
    'serviceDescription',
    'serviceFeatures',
    'serviceBenefits',
    'serviceCategories',
    'supplierName'
))
def test_highlight_block_contains_correct_fields(services_mapping, example):
    query = construct_query(services_mapping, build_query_params(keywords="some keywords"))

    assert "highlight" in query
    assert 'dmtext_' + example in query["highlight"]["fields"], example


class TestFieldFilters(object):
    def test_field_is_or_filter(self):
        assert field_is_or_filter(['a,b'])

    def test_field_is_or_filter_no_comma(self):
        assert not field_is_or_filter(['a'])

    def test_field_is_or_filter_multiple_values_no_comma(self):
        assert not field_is_or_filter(['a', 'b'])

    def test_field_is_or_filter_multiple_values(self):
        assert not field_is_or_filter(['a,b', 'b,c'])

    def test_or_field_filters(self, services_mapping):
        expected_value = [{"terms": {"dmfilter_filterName": ['Aa bb', 'Bb cc']}}]
        assert field_filters(services_mapping, 'filterName', ['Aa bb,Bb cc']) == expected_value

    def test_and_field_filters(self, services_mapping):
        expected_value = [
            {"term": {"dmfilter_filterName": 'Aa bb'}},
            {"term": {"dmfilter_filterName": 'Bb cc'}}
        ]
        assert field_filters(services_mapping, 'filterName', ['Aa bb', 'Bb cc']) == expected_value

    def test_field_filters_single_value(self, services_mapping):
        assert field_filters(services_mapping, 'filterName', ['Aa Bb']) == [{"term": {"dmfilter_filterName": 'Aa Bb'}}]

    def test_field_filters_multiple_and_values(self, services_mapping):
        expected_value = [
            {"term": {"dmfilter_filterName": 'Aa bb'}},
            {"term": {"dmfilter_filterName": 'Bb,Cc'}}
        ]
        assert field_filters(services_mapping, 'filterName', ['Aa bb', 'Bb,Cc']) == expected_value

    def test_field_filters_or_value(self, services_mapping):
        expected_value = [{"terms": {"dmfilter_filterName": ['Aa', 'Bb']}}]
        assert field_filters(services_mapping, 'filterName', ['Aa,Bb']) == expected_value


class TestFilterClause(object):
    def test_filter_ignores_non_filter_query_args(self, services_mapping):
        assert (
            filter_clause(services_mapping, MultiDict({'fieldName': ['Aa bb'], 'lot': ['saas']})) ==
            {'bool': {'must': []}}
        )

    def test_single_and_field(self, services_mapping):
        assert (
            filter_clause(services_mapping, MultiDict({'filter_fieldName': ['Aa bb'], 'lot': 'saas'})) ==
            {'bool': {'must': [{"term": {"dmfilter_fieldName": 'Aa bb'}}]}}
        )

    def test_single_or_field(self, services_mapping):
        assert (
            filter_clause(services_mapping, MultiDict({'filter_fieldName': ['Aa,Bb']})) ==
            {'bool': {'must': [{"terms": {"dmfilter_fieldName": ['Aa', 'Bb']}}]}}
        )

    def test_or_and_combination(self, services_mapping):
        bool_filter = filter_clause(services_mapping, MultiDict({
            'filter_andFieldName': ['Aa', 'bb'],
            'filter_orFieldName': ['Aa,Bb']
        }))

        assert {"terms": {"dmfilter_orFieldName": ['Aa', 'Bb']}} in bool_filter['bool']['must']
        assert {"term": {"dmfilter_andFieldName": 'Aa'}} in bool_filter['bool']['must']
        assert {"term": {"dmfilter_andFieldName": 'bb'}} in bool_filter['bool']['must']
