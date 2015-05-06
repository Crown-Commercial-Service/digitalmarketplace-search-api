from .conversions import strip_and_lowercase

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


def construct_query(query_args, page=100):
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

    query["size"] = page
    if "from" in query_args:
        query["from"] = query_args.get("from")

    return query


def highlight_clause():
    highlights = dict()
    highlights["fields"] = {}

    for field in TEXT_FIELDS:
        highlights["fields"][field] = {}

    return highlights


def is_filtered(query_args):
    if "serviceTypes" in query_args:
        return True
    if "lot" in query_args:
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
        "bool": {
            "must": build_term_filters(query_args)
        }
    }


def build_term_filters(query_args):
    must = []
    if "serviceTypes" in query_args:
        for service_type in extract_service_types(query_args):
            must.append({
                "term": {
                    "serviceTypesExact":
                        strip_and_lowercase(service_type)
                }
            })
    if "lot" in query_args:
        must.append({
            "term": {
                "lot": query_args["lot"]
            }
        })
    return must


def extract_service_types(query_args):
    return [
        service_type.strip()
        for service_type in query_args["serviceTypes"].split(',')
    ]
