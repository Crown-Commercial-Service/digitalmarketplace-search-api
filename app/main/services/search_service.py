import os

from elasticsearch import Elasticsearch, TransportError
from app.mapping import SERVICES_MAPPING
from app.main.services.response_formatters import \
    convert_es_status, convert_es_results, generate_pagination_links
from app.main.services.query_builder import construct_query
from flask import current_app, url_for

es_url = os.getenv('DM_ELASTICSEARCH_URL')
es = Elasticsearch(es_url)


def response(status_code, message):
    return {"status_code": status_code, "message": message}


def message(message):
    return {"message": message}


def refresh(index_name):
    try:
        es.indices.refresh(index_name)
        return message("acknowledged"), 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code


def create_index(index_name):
    try:
        es.indices.create(index=index_name, body=SERVICES_MAPPING)
        return message("acknowledged"), 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code


def delete_index(index_name):
    try:
        es.indices.delete(index=index_name)
        return message("acknowledged"), 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code


def fetch_by_id(index_name, doc_type, document_id):
    try:
        res = es.get(index_name, document_id, doc_type)
        return {"services": res}, 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code


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
        return message("acknowledged"), 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code


def status_for_index(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        return {"status": convert_es_status(res, index_name)}, 200
    except TransportError as e:
        return {"status": _get_an_error_message(e)}, e.status_code


def status_for_all_indexes():
    try:
        res = es.indices.status(index="_all", human=True)
        return {"status": res}, 200
    except TransportError as e:
        return {"status": _get_an_error_message(e)}, e.status_code


def keyword_search(index_name, doc_type, query_args):
    try:
        page_size = int(current_app.config['DM_SEARCH_PAGE_SIZE'])
        res = es.search(
            index=index_name,
            doc_type=doc_type,
            body=construct_query(query_args, page_size)
        )

        results = convert_es_results(res, query_args)

        url_for_search = lambda **kwargs: \
            url_for('.search', index_name=index_name, doc_type=doc_type,
                    **kwargs)
        return {
            "search": results,
            "links": generate_pagination_links(
                query_args, results['total'], page_size, url_for_search)
        }, 200
    except TransportError as e:
        return message(_get_an_error_message(e)), e.status_code
    except ValueError as e:
        return message(str(e)), 400


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
