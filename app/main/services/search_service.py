from flask import current_app, url_for
from elasticsearch import TransportError

from ... import elasticsearch_client as es
from app.mapping import SERVICES_MAPPING
from app.main.services.response_formatters import \
    convert_es_status, convert_es_results, generate_pagination_links
from app.main.services.query_builder import construct_query


def refresh(index_name):
    try:
        es.indices.refresh(index_name)
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def create_index(index_name):
    try:
        es.indices.create(index=index_name, body=SERVICES_MAPPING)
        return "acknowledged", 200
    except TransportError as e:
        if u'IndexAlreadyExistsException' in _get_an_error_message(e):
            return put_index_mapping(index_name)
        current_app.logger.error(
            "Failed to create the index %s: %s",
            index, _get_an_error_message(e)
        )
        return _get_an_error_message(e), e.status_code


def create_alias(alias_name, target_index):
    """Sets an alias for a given index

    If alias already exists it's removed from any existing indexes first.

    """

    try:
        es.indices.update_aliases({"actions": [
            {"remove": {"index": "_all", "alias": alias_name}},
            {"add": {"index": target_index, "alias": alias_name}}
        ]})
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def put_index_mapping(index_name):
    try:
        es.indices.put_mapping(
            index=index_name,
            doc_type="services",
            body=SERVICES_MAPPING["mappings"]["services"]
        )
        return "acknowledged", 200
    except TransportError as e:
        current_app.logger.error(
            "Failed to update the index mapping for %s: %s",
            index, _get_an_error_message(e)
        )
        return _get_an_error_message(e), e.status_code


def delete_index(index_name):
    try:
        es.indices.delete(index=index_name)
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def fetch_by_id(index_name, doc_type, document_id):
    try:
        res = es.get(index_name, document_id, doc_type)
        return res, 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def delete_by_id(index_name, doc_type, document_id):
    try:
        res = es.delete(index_name, doc_type, document_id)
        return res, 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def index(index_name, doc_type, document, document_id):
    try:
        es.index(
            index=index_name,
            id=document_id,
            doc_type=doc_type,
            body=document)
        return "acknowledged", 200
    except TransportError as e:
        current_app.logger.error(
            "Failed to index the document %s: %s",
            document_id, _get_an_error_message(e)
        )
        return _get_an_error_message(e), e.status_code


def status_for_index(index_name):
    try:
        res = es.indices.status(index=index_name, human=True)
        info = es.indices.get(index_name)
    except TransportError as e:
        return _get_an_error_message(e), e.status_code

    return convert_es_status(index_name, res, info), 200


def status_for_all_indexes():
    try:
        return status_for_index('_all')
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def core_search_and_aggregate(index_name, doc_type, query_args, search=False, aggregations=[]):
    try:
        page_size = int(current_app.config['DM_SEARCH_PAGE_SIZE'])
        es_search_kwargs = {'search_type': 'count'} if aggregations and not search else {}
        res = es.search(
            index=index_name,
            doc_type=doc_type,
            body=construct_query(query_args, aggregations, page_size),
            **es_search_kwargs
        )

        results = convert_es_results(res, query_args)

        def url_for_search(**kwargs):
            return url_for('.search', index_name=index_name, doc_type=doc_type, _external=True, **kwargs)

        response = {
            "meta": results['meta'],
            "services": results['services'],
            "links": generate_pagination_links(
                query_args, results['meta']['total'],
                page_size, url_for_search
            ),
        }

        if aggregations:
            response['aggregations'] = {}
            # Return aggregations in a slightly cleaner format.
            for k, v in res.get('aggregations', {}).items():
                response['aggregations'][k] = {d['key']: d['doc_count'] for d in v['buckets']}

        return response, 200

    except TransportError as e:
        return _get_an_error_message(e), e.status_code

    except ValueError as e:
        return str(e), 400


def search_with_keywords_and_filters(index_name, doc_type, query_args):
    return core_search_and_aggregate(index_name, doc_type, query_args, search=True)


def aggregations_with_keywords_and_filters(index_name, doc_type, query_args, aggregations=[]):
    return core_search_and_aggregate(index_name, doc_type, query_args, aggregations=aggregations)


def _get_an_error_message(exception):
    try:
        info = exception.info
    except AttributeError:
        return exception
    try:
        error = info['error']
    except (KeyError, TypeError):
        return info

    return error
