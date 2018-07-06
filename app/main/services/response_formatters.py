import math

from flask import current_app, jsonify


def convert_es_status(index_name, status_response, info_response=None):
    if index_name in ["_all", ""]:
        return {
            name: _convert_es_index_status(name, status_response, info_response or {})
            for name in status_response["indices"].keys()
        }
    else:
        return _convert_es_index_status(index_name, status_response, info_response or {})


def _convert_es_index_status(index_name, status_response, info_response):
    index_status = status_response['indices'].get(index_name, {})
    if not index_status:
        return index_status

    index_mapping = info_response.get(index_name, {}).get('mappings', {}).get("services", {})
    index_aliases = info_response.get(index_name, {}).get('aliases', {})

    return {
        'num_docs': index_status["primaries"].get("docs", {}).get("count"),
        'primary_size': index_status["primaries"]["store"]["size"],
        'mapping_version': index_mapping.get('_meta', {}).get('version'),
        'aliases': list(index_aliases.keys()),
    }


def _convert_es_result(mapping, es_result):
    # generate outgoing result dict only including es_result keys whose un-prefixed field name is in
    # mapping.response_fields, removing prefix in the process
    return {
        maybe_name_seq[0]: value
        for (prefix, *maybe_name_seq), value in (
            (prefixed_name.split("_", 1), value)
            for prefixed_name, value in es_result.items()
        )
        if prefix and maybe_name_seq and maybe_name_seq[0] in mapping.fields_by_prefix[mapping.response_field_prefix]
    }


def convert_es_results(mapping, results, query_args, aggregations=None, links=None):
    response = {
        "meta": {
            "query": query_args,
            "total": results["hits"]["total"],
            "took": results["took"],
        },
        "documents": [],
        "links": links
    }

    for document in results["hits"]["hits"]:
        if 'idOnly' in query_args:
            response["documents"].append({"id": document["_id"]})
        else:
            # populate result from document["_source"] object
            result = _convert_es_result(mapping, document["_source"])

            if "highlight" in document:
                # perform the same conversion for any highlight terms
                result["highlight"] = _convert_es_result(mapping, document["highlight"])

            response["documents"].append(result)
    if aggregations:
        response['aggregations'] = {
            k: {d['key']: d['doc_count'] for d in v['buckets']}
            for k, v in results.get('aggregations', {}).items()
        }
    return response


def generate_pagination_links_for_url(url_method, current_page, page_size, total_results):
    max_page = int(math.ceil(total_results / page_size))

    links = dict()
    if current_page > 1:
        links['prev'] = url_method(page=current_page - 1)
    if current_page < max_page:
        links['next'] = url_method(page=current_page + 1)
    return links


def api_response(data, status_code, key='message'):
    """Handle error codes.

    See http://elasticsearch-py.readthedocs.io/en/master/exceptions.html#elasticsearch.TransportError.status_code for
    an explaination of 'N/A' status code. elasticsearch-py client returns 'N/A' as status code if ES server cannot be
    reached, which is caught by `except TypeError` below.
    It's possible that the ElasticSearch library can also return other unexpected non-integer status codes, which will
    also get caught here, logged, and returned as part of the JSON.
    """
    try:
        if status_code // 100 == 2:
            return jsonify({key: data}), status_code
    except TypeError:
        current_app.logger.error(f'API response error: "{str(data)}" Unexpected status code: "{status_code}"')
        return jsonify(error=str(data), unexpectedStatusCode=status_code), 500
    return jsonify(error=data), status_code
