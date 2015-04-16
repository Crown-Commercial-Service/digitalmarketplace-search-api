from flask import jsonify, url_for, request, abort
from app.main import main
from app.main.services.search_service import keyword_search, \
    index, status_for_index, create_index, delete_index, \
    status_for_all_indexes
from app.main.services.conversions import strip_and_lowercase


@main.route('/')
def root():
    """Entry point for the API, show the resources that are available."""
    return jsonify(links=[
        {
            "rel": "query.gdm.index",
            "href": url_for('.search',
                            index_name="index-name",
                            doc_type="doc-type",
                            _external=True)
        }
    ]), 200


@main.route('/<string:index_name>/<string:doc_type>/search', methods=['GET'])
def search(index_name, doc_type):
    result = keyword_search(index_name, doc_type, request.args)
    response = jsonify({"search": result["message"]})
    response.status_code = result["status_code"]
    return response


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>',
            methods=['POST'])
def index_document(index_name, doc_type, service_id):
    json_payload = get_json_from_request('service')
    json_payload['serviceTypesExact'] = \
        create_exact_service_types(json_payload['serviceTypes'])
    result = index(
        index_name,
        doc_type,
        json_payload,
        service_id)
    response = jsonify({"results": result["message"]})
    response.status_code = result["status_code"]
    return response


@main.route('/<string:index_name>', methods=['PUT'])
def create(index_name):
    result = create_index(index_name)
    response = jsonify({"results": result["message"]})
    response.status_code = result["status_code"]
    return response


@main.route('/<string:index_name>', methods=['DELETE'])
def delete(index_name):
    result = delete_index(index_name)
    response = jsonify({"results": result["message"]})
    response.status_code = result["status_code"]
    return response


@main.route('/<string:index_name>/status', methods=['GET'])
def status(index_name):
    result = status_for_index(index_name)
    response = jsonify({"status": result["message"]})
    response.status_code = result["status_code"]
    return response


@main.route('/status', methods=['GET'])
def all_status():
    result = status_for_all_indexes()
    response = jsonify({"status": result["message"]})
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


def create_exact_service_types(service_types):
    fixed = []
    for i in service_types:
        fixed.append(strip_and_lowercase(i))
    return fixed
