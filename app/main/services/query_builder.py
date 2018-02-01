from itertools import chain


def construct_query(mapping, query_args, aggregations=[], page_size=100):
    """
        :param mapping: index's mapping as returned by `app.mapping.get_mapping`
        :param query_args: a MultiDict of request arguments
        :param aggregations: sequence of aggregations request arguments
        :param page_size: desired number of results per page. falsey values cause page & sorting-related parameters to
            be omitted (useful for e.g. `count` requests)
    """
    if not is_filtered(mapping, query_args):
        query = {
            "query": build_keywords_query(mapping, query_args)
        }
    else:
        query = {
            "query": {
                "bool": {
                    "must": build_keywords_query(mapping, query_args),
                    "filter": filter_clause(mapping, query_args)
                }
            }
        }

    if page_size:
        query["size"] = page_size

    if aggregations:
        aggregations = set(aggregations)
        missing_aggregations = aggregations.difference(
            mapping.fields_by_prefix.get(mapping.aggregatable_field_prefix) or frozenset()
        )
        if missing_aggregations:
            raise ValueError("Aggregations for `{}` are not supported.".format(', '.join(missing_aggregations)))

        query["size"] = 0  # We don't want any services returned, just aggregations
        query['aggregations'] = {
            x: {"terms": {"field": "_".join((mapping.aggregatable_field_prefix, x)), "size": 999999}}
            for x in aggregations
        }

    elif 'idOnly' in query_args:
        query['_source'] = False
    elif page_size:
        query["highlight"] = highlight_clause(mapping)
        query['sort'] = mapping.sort_clause

    if page_size and "page" in query_args:
        try:
            query["from"] = (int(query_args.get("page")) - 1) * page_size
        except ValueError:
            raise ValueError("Invalid page {}".format(query_args.get("page")))

    return query


def highlight_clause(mapping):
    highlights = {
        "encoder": "html",
        "pre_tags": ["<mark class='search-result-highlighted-text'>"],
        "post_tags": ["</mark>"]
    }
    highlights["fields"] = {}

    # Get all fields searched and allow non-matches to a max of the searchSummary limit
    for field in mapping.fields_by_prefix.get(mapping.text_search_field_prefix, ()):
        highlights["fields"]["_".join((mapping.text_search_field_prefix, field))] = {
            "number_of_fragments": 0,
            "no_match_size": 500
        }

    return highlights


def is_filtered(mapping, query_args):
    return bool(frozenset(
        maybe_name_seq[0]
        for prefix, *maybe_name_seq in (arg_key.split("_", 1) for arg_key in query_args.keys())
        if prefix == "filter" and maybe_name_seq  # maybe_name_seq could be an empty seq if no underscores were found
    ) & (mapping.fields_by_prefix.get(mapping.filter_field_prefix) or frozenset()))


def build_keywords_query(mapping, query_args):
    if "q" in query_args:
        return multi_match_clause(mapping, query_args["q"])
    else:
        return match_all_clause()


def multi_match_clause(mapping, keywords):
    """Builds a query string supporting basic query syntax.

    Uses "simple_query_string" with a predefined list of supported flags:

        OR          enables the `|` operator

        AND         enables the `+` operator. AND is a default operator, so
                    adding `+` doesn't affect the results.

        NOT         enables the `-` operator

        WHITESPACE  allows using whitespace escape sequences. `-` operator
                    doesn't work without the WHITESPACE flag possibly due to
                    a bug in the current (1.6) version of Elasticsearch.

        PHRASE      enables `"` to group tokens into phrases

        ESCAPE      allows escaping reserved characters with `\`

    (https://www.elastic.co/guide/en/elasticsearch/reference/1.6/query-dsl-simple-query-string-query.html)

    "simple_query_string" doesn't support "use_dis_max" flag.

    """
    return {
        "simple_query_string": {
            "query": keywords,
            "fields": [
                "_".join((mapping.text_search_field_prefix, field_name))
                for field_name in mapping.fields_by_prefix.get(mapping.text_search_field_prefix, ())
            ],
            "default_operator": "and",
            "flags": "OR|AND|NOT|PHRASE|ESCAPE|WHITESPACE"
        }
    }


def match_all_clause():
    return {
        "match_all": {}
    }


def field_is_or_filter(field_values):
    return (len(field_values) == 1) and ("," in field_values[0])


def field_filters(mapping, arg_field_name, field_values):
    """Build a list of Elasticsearch filters for the given field."""
    field_name = "_".join((mapping.filter_field_prefix, arg_field_name))
    if field_is_or_filter(field_values):
        return or_field_filters(field_name, field_values)
    else:
        return and_field_filters(field_name, field_values)


def or_field_filters(field_name, field_values):
    """OR filter returns documents that contain a field matching any of the values.

    Returns a list containing a single Elasticsearch "terms" filter.
    "terms" filter matches the given field with any of the values.

    "bool" execution generates a term filter (which is cached) for each term,
    and wraps those in a bool filter. This way each individual value match is
    cached (as opposed to the default of caching the whole filter result) and
    the cache can be reused in different combinations of values.

    (https://www.elastic.co/guide/en/elasticsearch/reference/1.6/query-dsl-terms-filter.html)

    """
    return [
        {
            "terms": {
                field_name: field_values[0].split(","),
            },
        },
    ]


def and_field_filters(field_name, field_values):
    """AND filter returns documents that contain fields matching all of the values.

    Returns a list of "term" filters: one for each of the filter values.

    """
    return [
        {
            "term": {
                field_name: value,
            }
        }
        for value in field_values
    ]


def filter_clause(mapping, query_args):
    """Build a filter clause from the query arguments.

    Iterates over the request.args MultiDict and builds
    OR or AND filters with values for each field.

    Since the field values are grouped within the MultiDict
    each field will be either an OR or an AND filter.

    The resulting filter lists are joined into a single flat
    list of filters that is wrapped with a `bool` `must` filter.

    This means that all individual field filters must match at
    the same time, but depending on the particular field filter
    type the field value has to match either all filter values or
    just any one of them.

    """
    return {
        "bool": {
            "must": list(chain.from_iterable(
                field_filters(mapping, maybe_name_seq[0], values)
                for (prefix, *maybe_name_seq), values in (
                    (arg_key.split("_", 1), values)
                    for arg_key, values in query_args.lists()
                )
                if prefix == "filter" and maybe_name_seq  # maybe_name_seq could be an empty seq if no underscores were
                                                          # found
            )),
        },
    }
