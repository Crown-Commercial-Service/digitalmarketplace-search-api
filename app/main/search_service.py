import os
from elasticsearch import Elasticsearch, TransportError
from ..mapping import SERVICES_MAPPING
import re

es_url = os.getenv('DM_ELASTICSEARCH_URL')
es = Elasticsearch(es_url)


def response(status_code, message):
    return {"status_code": status_code, "message": message}


def create_index(index_name):
    try:
        es.indices.create(index=index_name, body=SERVICES_MAPPING)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def delete_index(index_name):
    try:
        es.indices.delete(index=index_name)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def index(index_name, doc_type, document, document_id):
    try:
        es.index(index=index_name, id=document_id, doc_type=doc_type, body=document)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def index_status(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        return response(200, res)
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def status():
    return index_status("_all")


def keyword_search(index_name, doc_type, query_args):
    try:
        print query_args
        res = es.search(index=index_name, doc_type=doc_type, body=query_builder(query_args))
        return response(200, convert_es_results(res, query_args))
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def strip_and_lowercase(value):
    return re.sub(r'\s+', '', value).lower()


def query_builder(query_args):
    if "category" in query_args and "q" in query_args:
        base_query = {
            "query": {
                "filtered": {
                    "query": multi_match(query_args["q"]),
                    "filter": {
                        "term": {"serviceTypesExact": strip_and_lowercase(query_args["category"])}
                    }
                }
            }
        }
    elif "q" in query_args and "category" not in query_args:
        base_query = {
            "query": multi_match(query_args["q"])
        }
    elif "category" in query_args and "q" not in query_args:
        base_query = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "term": {"serviceTypesExact": strip_and_lowercase(query_args["category"])}
                    }
                }
            }
        }
    else:
        base_query = {
            "query": {
                "match_all": {}
            }
        }

    base_query["highlight"] = {
        "fields": {
            "id": {},
            "lot": {},
            "serviceName": {},
            "serviceSummary": {},
            "serviceFeatures": {},
            "serviceBenefits": {},
            "serviceTypes": {},
            "supplierName": {}
        }
    }

    print base_query
    return base_query


def multi_match(keywords):
    return {
        "multi_match": {
            "query": keywords,
            "fields": [
                "id",
                "lot",
                "serviceName",
                "serviceSummary",
                "serviceFeatures",
                "serviceBenefits",
                "serviceTypes",
                "supplierName"
            ],
            "operator": "and"
        }
    }


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


def convert_es_results(results, query_args):
    services = []
    total = results["hits"]["total"]
    took = results["took"]
    print results

    for service in results["hits"]["hits"]:
        services.append({
            "id": service["_source"]["id"],
            "lot": service["_source"]["lot"],
            "supplierName": service["_source"]["supplierName"],
            "serviceName": service["_source"]["serviceName"],
            "serviceSummary": service["_source"]["serviceSummary"],
            "serviceTypes": service["_source"]["serviceTypes"],
            "highlight": service["highlight"]
        })

    return {
        "query": query_args,
        "total": total,
        "took": took,
        "services": services
    }