from .conversions import strip_and_lowercase

# These two arrays should be part of a mapping definition
from werkzeug.datastructures import MultiDict

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

FILTER_FIELDS = [
    "lot",
    "serviceTypes",
    "freeOption",
    "trialOption",
    "minimumContractPeriod",
    "supportForThirdParties",
    "selfServiceProvisioning",
    "datacentresEUCode",
    "dataBackupRecovery",
    "dataExtractionRemoval",
    "networksConnected",
    "apiAccess",
    "openStandardsSupported",
    "openSource",
    "persistentStorage",
    "guaranteedResources",
    "elasticCloud"
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
    print query
    return query


def highlight_clause():
    highlights = dict()
    highlights["fields"] = {}

    for field in TEXT_FIELDS:
        highlights["fields"][field] = {}

    return highlights


def is_filtered(query_args):
    if "filter_serviceTypes" in query_args:
        return True
    if "filter_lot" in query_args:
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
    # and_filters = MultiDict()
    #
    # filters = [
    #     (format_key(param[0]), param[1])
    #     for param in query_args.iterlists() if
    #     param[0].startswith("filter_")]
    #
    # for a_filter in filters:
    #     if len(a_filter[1]) > 0:
    #         and_filters.add(a_filter[0], a_filter[1])

    return {
        "bool": {
            "must": get_filter_params(query_args)
        }
    }


def get_filter_params(query_args):
    terms = []
    filters = [
        (format_key(param[0]), param[1])
        for param in query_args.iterlists() if
        param[0].startswith("filter_")]

    for a_filter in filters:
        for filter_value in a_filter[1]:
            terms.append({
                "term": {
                    a_filter[0]: strip_and_lowercase(filter_value)
                }
            })
    return terms


def format_key(key):
    return key.replace("filter_", '') + "Exact"
