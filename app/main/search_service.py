import os
from elasticsearch import Elasticsearch

# Setup
es_url = os.getenv('DM_ELASTICSEARCH_URL')
es = Elasticsearch(es_url)


# Basic keyword query without filters endpoint - may not be required as the
# filtered query gives the same results if only a keyword query is supplied
#
# I'm leaving it here for now though
#
# def keyword_query(query, start_from=0, size=10):
#     res = es.search(index="services",
#                     body={
#                         "from": start_from, "size": size,
#                         "fields": ["id", "serviceName", "lot",
#                                    "serviceSummary"],
#                         "query": {
#                             "multi_match": {
#                                 "query": query,
#                                 "fields": ["serviceName",
#                                            "serviceSummary",
#                                            "serviceFeatures",
#                                            "serviceBenefits"],
#                                 "operator": "or"
#                             }
#                         }
#                     }
#                     )
#     return res


def keyword_query_with_filters(request_args, start_from=0, size=10):
    query = request_args["q"]
    filters = []
    for k, v in request_args.iteritems():
        # Do not include the query string as a filter
        if k == "q":
            continue
        filters.append({"term": {k: v.lower()}})
    res = es.search(index="services",
                    body={
                        "from": start_from, "size": size,
                        "fields": ["id", "serviceName", "lot",
                                   "serviceSummary"],
                        "query": {
                            "filtered": {
                                "query": {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["serviceName",
                                                   "serviceSummary",
                                                   "serviceFeatures",
                                                   "serviceBenefits"],
                                        "operator": "or"
                                    }
                                },
                                "filter": {
                                    "bool": {"must": filters}
                                }
                            }
                        }
                    }
                    )
    return res
