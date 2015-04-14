def format_status(es_response, index_name):
    index_status = es_response["indices"][index_name]

    status = {}

    if "docs" in index_status:
        status["num_docs"] = index_status["docs"]["num_docs"]

    status["primary_size"] = index_status["index"]["primary_size"]

    return {
        "status": status
    }
