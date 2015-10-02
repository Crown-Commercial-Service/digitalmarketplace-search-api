from flask import jsonify, url_for, request, abort
from app.main import main
from app.main.services.search_service import keyword_search, \
    index, status_for_index, create_index, delete_index, \
    fetch_by_id, delete_by_id, create_alias
from app.main.services.process_request_json import \
    convert_request_json_into_index_json


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
    result, status_code = keyword_search(index_name, doc_type, request.args)

    if status_code == 200:
        return jsonify(meta=result['meta'],
                       services=result['services'],
                       links=result['links']), status_code
    else:
        return api_response(result, status_code)


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>',
            methods=['PUT'])
def index_document(index_name, doc_type, service_id):
    json_payload = get_json_from_request('service')
    index_json = convert_request_json_into_index_json(json_payload)
    result, status_code = index(index_name, doc_type, index_json, service_id)

    return api_response(result, status_code)


@main.route('/<string:index_name>', methods=['PUT'])
def create(index_name):
    create_type = get_json_from_request('type')
    if create_type == 'index':
        result, status_code = create_index(index_name)
    elif create_type == 'alias':
        alias_target = get_json_from_request('target')
        result, status_code = create_alias(index_name, alias_target)
    else:
        abort(400, "Unrecognized 'type' value. Expected 'index' or 'alias'")

    return api_response(result, status_code)


@main.route('/<string:index_name>', methods=['DELETE'])
def delete(index_name):
    result, status_code = delete_index(index_name)

    return api_response(result, status_code)


@main.route('/<string:index_name>', methods=['GET'])
def status(index_name):
    result, status_code = status_for_index(index_name)

    return api_response(result, status_code, key='status')


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>',
            methods=['GET'])
def fetch_service(index_name, doc_type, service_id):
    result, status_code = fetch_by_id(index_name, doc_type, service_id)

    if status_code == 200:
        return jsonify(services=result), status_code
    else:
        return api_response(result, status_code)


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>',
            methods=['DELETE'])
def delete_service(index_name, doc_type, service_id):
    result, status_code = delete_by_id(index_name, doc_type, service_id)

    return api_response(result, status_code)


def api_response(data, status_code, key='message'):
    if status_code // 100 == 2:
        return jsonify({key: data}), status_code
    else:
        return jsonify(error=data), status_code


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
