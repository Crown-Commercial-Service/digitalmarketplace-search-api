from .conversions import strip_and_lowercase
from ...mapping import TEXT_FIELDS, FILTER_FIELDS


def construct_query(query_args, page_size=100):
    if not is_filtered(query_args):
        query = {
            "query": build_keywords_query(query_args)
        }
    else:
        query = {
            "query": {
                "filtered": {
                    "query": build_keywords_query(query_args),
                    "filter": filter_clause(query_args)
                }
            }

        }
    query["highlight"] = highlight_clause()

    query["size"] = page_size
    if "page" in query_args:
        try:
            query["from"] = (int(query_args.get("page")) - 1) * page_size
        except ValueError:
            raise ValueError("Invalid page {}".format(query_args.get("page")))

    return query


def highlight_clause():
    highlights = {
        "encoder": "html",
        "pre_tags": ["<em class='search-result-highlighted-text'>"],
        "post_tags": ["</em>"]
    }
    highlights["fields"] = {}

    for field in TEXT_FIELDS:
        highlights["fields"][field] = {}

    return highlights


def is_filtered(query_args):
    return len(set(query_args.keys()).intersection(
        ["filter_" + field for field in FILTER_FIELDS])) > 0


def build_keywords_query(query_args):
    if "q" in query_args:
        return multi_match_clause(query_args["q"])
    else:
        return match_all_clause()


def multi_match_clause(keywords):
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
            "fields": TEXT_FIELDS,
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


def field_filters(field_name, field_values):
    """Build a list of Elasticsearch filters for the given field."""
    if field_is_or_filter(field_values):
        field_values = field_values[0].split(",")
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
    terms = [strip_and_lowercase(value) for value in field_values]
    return [{
        "terms": {
            field_name: terms,
            "execution": "bool"
        }
    }]


def and_field_filters(field_name, field_values):
    """AND filter returns documents that contain fields matching all of the values.

    Returns a list of "term" filters: one for each of the filter values.

    """
    return [{
        "term": {
            field_name: strip_and_lowercase(value)
        }
    } for value in field_values]


def filter_clause(query_args):
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

    query_filters = []
    for field, values in query_args.lists():
        if field.startswith("filter"):
            query_filters.extend(field_filters(field, values))

    filters = {
        "bool": {
            "must": query_filters
        }
    }

    return filters
