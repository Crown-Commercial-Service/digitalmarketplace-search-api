import re

TEXT_FIELDS = [
    "id",
    "lot",
    "serviceName",
    "serviceSummary",
    "serviceFeatures",
    "serviceBenefits",
    "serviceTypes",
    "supplierName"
]


def construct_query(query_args):
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
    return query


def highlight_clause():
    hightlights = {}
    hightlights["fields"] = {}

    for field in TEXT_FIELDS:
        hightlights["fields"][field] = {}

    return hightlights


def is_filtered(query_args):
    if "category" in query_args:
        return True
    return False


def build_keywords_query(query_args):
    if "q" in query_args:
        return multi_match_clause(query_args["q"])
    else:
        return match_all_clause()


def multi_match_clause(keywords):
    return {
        "multi_match": {
            "query": keywords,
            "fields": TEXT_FIELDS,
            "operator": "and"
        }
    }


def match_all_clause():
    return {
        "match_all": {}
    }


def filter_clause(query_args):
    return {
        "term": {
            "serviceTypesExact": strip_and_lowercase(
                query_args["category"])
        }
    }


def strip_and_lowercase(value):
    return re.sub(r'[\s+|\W+]', '', value).lower()
