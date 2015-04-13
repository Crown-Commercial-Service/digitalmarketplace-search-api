import os
from elasticsearch import Elasticsearch, TransportError
from ..mapping import SERVICES_MAPPING

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


def status(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        print(res)
        return response(200, res)
    except TransportError as e:
        return response(e.status_code, e.info["error"])


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
