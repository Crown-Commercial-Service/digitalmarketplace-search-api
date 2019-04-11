from elasticsearch import TransportError
from flask import current_app, escape, url_for

from dmutils.timing import logged_duration_for_external_request

import app.mapping
from app.main.services.response_formatters import convert_es_status, convert_es_results, generate_pagination_links
from app.main.services.query_builder import construct_query

from ... import elasticsearch_client as es


def refresh(index_name):
    try:
        with logged_duration_for_external_request('es'):
            es.indices.refresh(index_name)
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def create_index(index_name, mapping_name):
    mapping_definition = app.mapping.load_mapping_definition(mapping_name)
    try:
        with logged_duration_for_external_request('es'):
            es.indices.create(index=index_name, body=mapping_definition)
        return "acknowledged", 200
    except TransportError as e:
        current_app.logger.warning(
            "Failed to create the index %s: %s",
            index, _get_an_error_message(e)
        )
        return _get_an_error_message(e), e.status_code


def create_alias(alias_name, target_index):
    """Sets an alias for a given index

    If alias already exists it's removed from any existing indexes first.

    """

    try:
        with logged_duration_for_external_request('es'):
            es.indices.update_aliases({"actions": [
                {"remove": {"index": "_all", "alias": alias_name}},
                {"add": {"index": target_index, "alias": alias_name}}
            ]})
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def delete_index(index_name):
    try:
        with logged_duration_for_external_request('es'):
            es.indices.delete(index=index_name)
        return "acknowledged", 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def fetch_by_id(index_name, doc_type, document_id):
    try:
        with logged_duration_for_external_request('es'):
            res = es.get(index=index_name, doc_type=doc_type, id=document_id)
        return res, 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def delete_by_id(index_name, doc_type, document_id):
    try:
        with logged_duration_for_external_request('es'):
            res = es.delete(index=index_name, doc_type=doc_type, id=document_id)
        return res, 200
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def index(index_name, doc_type, document, document_id):
    try:
        with logged_duration_for_external_request('es'):
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
        with logged_duration_for_external_request('es'):
            res = es.indices.stats(index=index_name, human=True)
        with logged_duration_for_external_request('es'):
            info = es.indices.get(index_name)
    except TransportError as e:
        return _get_an_error_message(e), e.status_code

    return convert_es_status(index_name, res, info), 200


def status_for_all_indexes():
    try:
        return status_for_index('_all')
    except TransportError as e:
        return _get_an_error_message(e), e.status_code


def _page_404_response(requested_page):
    return "{} does not exist for this search".format(
        "This page" if requested_page is None else "Page {}".format(requested_page)
    ), 404


def core_search_and_aggregate(index_name, doc_type, query_args, search=False, aggregations=[]):  # noqa: C901
    try:
        mapping = app.mapping.get_mapping(index_name, doc_type)
        page_size = int(current_app.config['DM_SEARCH_PAGE_SIZE'])
        if 'idOnly' in query_args:
            page_size *= int(current_app.config['DM_ID_ONLY_SEARCH_PAGE_SIZE_MULTIPLIER'])

        es_search_kwargs = {'search_type': 'dfs_query_then_fetch'} if search else {}
        constructed_query = construct_query(mapping, query_args, aggregations, page_size)
        with logged_duration_for_external_request('es'):
            res = es.search(index=index_name, doc_type=doc_type, body=constructed_query, **es_search_kwargs)

        results = convert_es_results(mapping, res, query_args)

        # WORKAROUND: In Elasticsearch 6 the default highlighter will only return the first sentence if the
        # highlighter finds no terms to mark. This hack basically makes sure that the always get the full
        # service description in this case. See https://github.com/elastic/elasticsearch/issues/41066.
        # Should be fixed in > v6.7.2 :fingers_crossed:.
        escape_field = "serviceDescription" if doc_type == "services" else "summary"
        for document in results["documents"]:
            if "highlight" not in document:
                break
            if len(document["highlight"][escape_field][0]) < len(document[escape_field]):
                escaped_description = escape(document[escape_field])
                # escape doesn't escape / but Elasticsearch does
                escaped_description = escaped_description.translate({ord("/"): "&#x2F;"})
                document["highlight"][escape_field] = [escaped_description]

        def url_for_search(**kwargs):
            return url_for('.search', index_name=index_name, doc_type=doc_type, _external=True, **kwargs)

        response = {
            "meta": results['meta'],
            "documents": results['documents'],
            "links": generate_pagination_links(
                query_args, results['meta']['total'],
                page_size, url_for_search
            ),
        }

        if aggregations:
            # Return aggregations in a slightly cleaner format.
            response['aggregations'] = {
                k: {d['key']: d['doc_count'] for d in v['buckets']}
                for k, v in res.get('aggregations', {}).items()
            }

        # determine whether we're actually off the end of the results. ES handles this as a result-less-yet-happy
        # response, but we probably want to turn it into a 404 not least so we can match our behaviour when fetching
        # beyond the `max_result_window` below
        if search and constructed_query.get("from") and not response["documents"]:
            return _page_404_response(query_args.get("page", None))

        return response, 200

    except TransportError as e:
        try:
            root_causes = getattr(e, "info", {}).get("error", {}).get("root_cause", {})
        except AttributeError:
            # Catch if the contents of 'info' has no ability to get attributes
            return _get_an_error_message(e), e.status_code

        if root_causes and root_causes[0].get("reason").startswith("Result window is too large"):
            # in this case we have to fire off another request to determine how we should handle this error...
            # (note minor race condition possible if index is modified between the original call and this one)
            try:
                body = construct_query(mapping, query_args, page_size=None)
                with logged_duration_for_external_request('es'):
                    result_count = es.count(
                        index=index_name,
                        doc_type=doc_type,
                        body=body
                    )["count"]
            except TransportError as e:
                return _get_an_error_message(e), e.status_code
            else:
                if result_count < constructed_query.get("from", 0):
                    # there genuinely aren't enough results for this number of pages, so this should be a 404
                    return _page_404_response(query_args.get("page", None))
                # else fall through and allow this to 500 - we probably don't have max_result_window set high enough
                # for the number of results it's possible to access using this index.
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
        return str(exception)
    try:
        error = info['error']
    except (KeyError, TypeError):
        return info
    try:  # ES5 errors are dicts; get the reason for the error so that the log formatter only gets a string.
        root_cause = error['root_cause'][0]
        type = root_cause.get('type', '<unknown type>')
        reason = root_cause.get('reason', '<unknown reason>')
        index = root_cause.get('index', '<no index>')

        return '{}: {} ({})'.format(type, reason, index)

    except (KeyError, IndexError):
        pass

    return error
