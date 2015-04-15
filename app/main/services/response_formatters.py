from .query_builder import TEXT_FIELDS


def convert_es_status(es_response, index_name):
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
        "services": services
    }


def append_field_if_present(result, service, field):
    if field in service:
        result[field] = service[field]
