import math


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
        maybe_name[0]: value
        for (prefix, *maybe_name), value in (
            (prefixed_name.split("_", 1), value)
            for prefixed_name, value in es_result.items()
        )
        if prefix and maybe_name and maybe_name[0] in mapping.fields_by_prefix[mapping.response_field_prefix]
    }


def convert_es_results(mapping, results, query_args):
    services = []

    for service in results["hits"]["hits"]:
        if 'idOnly' in query_args:
            services.append({"id": service["_id"]})
        else:
            # populate result from service["_source"] object
            result = _convert_es_result(mapping, service["_source"])

            if "highlight" in service:
                # perform the same conversion for any highlight terms
                result["highlight"] = _convert_es_result(mapping, service["highlight"])

            services.append(result)

    return {
        "meta": {
            "query": query_args,
            "total": results["hits"]["total"],
            "took": results["took"],
        },
        "services": services,
    }


def generate_pagination_links(query_args, total, page_size, url_for_search):
    page = int(query_args.get('page', 1))
    max_page = int(math.ceil(float(total) / page_size))
    args_no_page = {k: v for k, v in query_args.lists() if k != 'page'}

    links = dict()
    if page > 1:
        links['prev'] = url_for_search(page=page - 1, **args_no_page)
    if page < max_page:
        links['next'] = url_for_search(page=page + 1, **args_no_page)
    return links
