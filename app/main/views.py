from flask import jsonify, url_for, request, abort
from . import main, search_service
from .search_result_formatters import SearchResults


@main.route('/')
def index():
    """Entry point for the API, show the resources that are available."""
    return jsonify(links=[
        {
            "rel": "query.gdm.index",
            "href": url_for('.keyword_query_with_optional_filters',
                            _external=True)
        }
    ]), 200


@main.route('/search', methods=['GET'])
def keyword_query_with_optional_filters():
    response = search_service.keyword_query_with_filters(request.args)
    search_results_obj = SearchResults(response)
    return jsonify(search_results_obj.get_results())

@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>', methods=['POST'])
def index_document(index_name, doc_type, service_id):
    json_payload = get_json_from_request('service')
    result = search_service.index(index_name, doc_type, json_payload, service_id)
    response = jsonify({"message": result["message"]})
    response.status_code = result["status_code"]
    return response

@main.route('/<string:index_name>', methods=['PUT'])
def create_index(index_name):
    result = search_service.create_index(index_name)
    response = jsonify({"message": result["message"]})
    response.status_code = result["status_code"]
    return response

@main.route('/<string:index_name>', methods=['DELETE'])
def delete_index(index_name):
    result = search_service.delete_index(index_name)
    response = jsonify({"message": result["message"]})
    response.status_code = result["status_code"]
    return response

@main.route('/<string:index_name>/status', methods=['GET'])
def status(index_name):
    result = search_service.status(index_name)
    response = jsonify({"message": result["message"]})
    response.status_code = result["status_code"]
    return response


def check_json_from_request(request):
    if request.content_type not in ['application/json',
                                    'application/json; charset=UTF-8']:
        abort(400, "Unexpected Content-Type, expecting 'application/json'")
    data = request.get_json()
    if data is None:
        abort(400, "Invalid JSON; must be a valid JSON object")
    return data


def json_has_required_keys(data, keys):
    for key in keys:
        if key not in data.keys():
            abort(400, "Invalid JSON must have '%s' key(s)" % keys)


def get_json_from_request(root_field):
    payload = check_json_from_request(request)
    json_has_required_keys(payload, [root_field])
    update_json = payload[root_field]
    return update_json