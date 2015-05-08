import math

from .query_builder import TEXT_FIELDS


def convert_es_status(es_response, index_name):
    if index_name in ["_all", ""]:
        return [
            _convert_es_index_status(es_response, name)
            for name in es_response["indices"].keys()
        ]
    else:
        return _convert_es_index_status(es_response, index_name)


def _convert_es_index_status(es_response, index_name):
    index_status = es_response["indices"][index_name]

    status = {}

    if "docs" in index_status:
        status["num_docs"] = index_status["docs"]["num_docs"]

    status["primary_size"] = index_status["index"]["primary_size"]

    return status


def convert_es_results(results, query_args):
    services = []
    total = results["hits"]["total"]
    took = results["took"]

    for service in results["hits"]["hits"]:
        result = {}
        for field in TEXT_FIELDS:
            append_field_if_present(result, service["_source"], field)

        append_field_if_present(result, service, "highlight")

        services.append(result)

    return {
        "query": query_args,
        "total": total,
        "took": took,
        "services": services,
    }


def generate_pagination_links(query_args, total, page_size, url_for_search):
    page = int(query_args.get('page', 1))
    max_page = int(math.ceil(float(total) / page_size))
    args_no_page = {k: v for k, v in query_args.lists() if k != 'page'}

    links = dict()
    if page > 1:
        links['prev'] = url_for_search(page=page-1, **args_no_page)
    if page < max_page:
        links['next'] = url_for_search(page=page+1, **args_no_page)
    return links


def append_field_if_present(result, service, field):
    if field in service:
        result[field] = service[field]
