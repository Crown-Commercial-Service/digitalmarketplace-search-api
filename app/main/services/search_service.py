import os

from elasticsearch import Elasticsearch, TransportError
from app.mapping import SERVICES_MAPPING
from app.main.services.response_formatters import \
    convert_es_status, convert_es_results
from app.main.services.query_builder import construct_query
from flask import current_app

es_url = os.getenv('DM_ELASTICSEARCH_URL')
es = Elasticsearch(es_url)


def refresh(index_name):
    return es.indices.refresh(index_name)


def response(status_code, message):
    return {"status_code": status_code, "message": message}


def create_index(index_name):
    try:
        es.indices.create(index=index_name, body=SERVICES_MAPPING)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def delete_index(index_name):
    try:
        es.indices.delete(index=index_name)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def fetch_by_id(index_name, doc_type, document_id):
    try:
        res = es.get(index_name, document_id, doc_type)
        return response(200, res)
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def delete_by_id(index_name, doc_type, document_id):
    try:
        res = es.delete(index_name, doc_type, document_id)
        return response(200, res)
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def index(index_name, doc_type, document, document_id):
    try:
        es.index(
            index=index_name,
            id=document_id,
            doc_type=doc_type,
            body=document)
        return response(200, "acknowledged")
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def status_for_index(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        return response(200, convert_es_status(res, index_name))
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))


def status_for_all_indexes():
    return status_for_index("_all")


def keyword_search(index_name, doc_type, query_args):
    try:
        res = es.search(
            index=index_name,
            doc_type=doc_type,
            body=construct_query(
                query_args,
                current_app.config['DM_SEARCH_PAGE_SIZE'])
        )
        return response(200, convert_es_results(res, query_args))
    except TransportError as e:
        return response(e.status_code, _get_an_error_message(e))
    except ValueError as e:
        return response(400, e.message)


def _get_an_error_message(exception):
    try:
        info = exception.info
    except:
        return exception
    try:
        error = info['error']
    except:
        return info
    return error
