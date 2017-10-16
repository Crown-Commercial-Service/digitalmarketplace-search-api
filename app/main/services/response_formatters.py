import math

import app.mapping


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


def convert_es_results(results, query_args):
    services = []
    total = results["hits"]["total"]
    took = results["took"]

    for service in results["hits"]["hits"]:
        result = {}
        for field in app.mapping.get_services_mapping().text_fields:
            append_field_if_present(result, service["_source"], field)

        append_field_if_present(result, service, "highlight")

        services.append(result)

    return {
        "meta": {
            "query": query_args,
            "total": total,
            "took": took
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


def append_field_if_present(result, service, field):
    if field in service:
        result[field] = service[field]
