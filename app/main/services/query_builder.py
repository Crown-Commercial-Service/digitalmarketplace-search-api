from .conversions import strip_and_lowercase

# These two arrays should be part of a mapping definition
TEXT_FIELDS = [
    "id",
    "lot",
    "serviceName",
    "serviceSummary",
    "serviceFeatures",
    "serviceBenefits",
    "serviceTypes",
    "supplierName",
    "frameworkName"
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


class QueryFilter(object):
    """
    Class to encapsulate a query multidict from flask

    Filter name is the key from the multidict.

    Multidict is map of key to a list, to encompass
    multiple HTTP params of same name

    Filter value is derived from the mutlidict
        - Single string value is an AND filter
        - Single string value, that contains commas is
        treated as a CSV and becomes
        an OR filter with each string a single term
        - Multiple values is treated as an AND with
        several terms for that key

    Examples:
        filter_lot=saas&filter_lot=paas => lot == saas AND lot = paas
        filter_lot=saas,paas => lot == saas OR lot ==saas
        filter_lot=saas => lot == saas


    """
    OR = "or"
    AND = "and"

    def __init__(self, field, values):
        self.filter_field = field
        self.filter_values = values
        self.filter_type = self.__filter_type()

    def __filter_type(self):
        # multiple values for same key is an AND filter
        if len(self.filter_values) > 1:
            return self.AND
        if len(self.filter_values) == 1:
            if "," in self.filter_values[0]:
                # comma separated single value for a field is an OR filter
                return self.OR
            # single value for a key is an AND filter
            return self.AND

    def is_and_filter(self):
        return self.filter_type == self.AND

    def is_or_filter(self):
        return self.filter_type == self.OR

    def terms(self):
        terms = []
        term_values = []

        if self.is_or_filter():
            term_values = self.filter_values[0].split(",")
        if self.is_and_filter():
            term_values = self.filter_values

        for value in term_values:
            terms.append({
                "term": {
                    self.filter_field: strip_and_lowercase(value)
                }
            })
        return terms

    def __str__(self):
        return str({
            "filter_field": self.filter_field,
            "filter_values": self.filter_values,
            "filter_type": self.filter_type,
            "filter_terms": self.terms(),
        })


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
    highlights = dict({
        "pre_tags": ["<em class='search-result-highlighted-text'>"],
        "post_tags": ["</em>"]
    })
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
    return {
        "query_string": {
            "query": keywords,
            "fields": TEXT_FIELDS,
            "use_dis_max": True,
        }
    }


def match_all_clause():
    return {
        "match_all": {}
    }


def filter_clause(query_args):
    and_filters = []
    or_filters = []

    query_filters = [QueryFilter(field, values)
                     for field, values in query_args.lists()
                     if field.startswith("filter")]
    filters = {
        "bool": {}
    }

    for each_filter in query_filters:
        if each_filter.is_and_filter():
            and_filters += each_filter.terms()
        if each_filter.is_or_filter():
            or_filters += each_filter.terms()

    if and_filters:
        filters["bool"]["must"] = and_filters

    if or_filters:
        filters["bool"]["should"] = or_filters

    return filters
