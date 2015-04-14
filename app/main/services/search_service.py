import os
import re

from elasticsearch import Elasticsearch, TransportError
from app.mapping import SERVICES_MAPPING
from app.main.services.response_formatters import format_status

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
        es.index(
            index=index_name,
            id=document_id,
            doc_type=doc_type,
            body=document)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def status_for_index(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        return response(200, format_status(res, index_name))
    except TransportError as e:
        return response(e.status_code, e.info["error"])


def status_for_all_indexes():
    return status_for_index("_all")


def keyword_search(index_name, doc_type, query_args):
    try:
        res = es.search(
            index=index_name,
            doc_type=doc_type,
            body=query_builder(query_args))
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
                        "term": {"serviceTypesExact": strip_and_lowercase(
                            query_args["category"])}
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
                        "term": {"serviceTypesExact": strip_and_lowercase(
                            query_args["category"])}
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
