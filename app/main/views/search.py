from flask import jsonify, request, abort, current_app
from app.main import main
from app.main.services.search_service import search_with_keywords_and_filters, aggregations_with_keywords_and_filters, \
    index, status_for_index, create_index, delete_index, \
    fetch_by_id, delete_by_id, create_alias
from app.main.services.process_request_json import \
    convert_request_json_into_index_json
import app


@main.route('/<string:index_name>/<string:doc_type>/search', methods=['GET'])
def search(index_name, doc_type):
    result, status_code = search_with_keywords_and_filters(index_name, doc_type, request.args)

    if status_code == 200:
        return jsonify(meta=result['meta'],
                       services=result['services'],
                       links=result['links']), status_code
    else:
        return api_response(result, status_code)


@main.route('/<string:index_name>/<string:doc_type>/aggregations', methods=['GET'])
def aggregations(index_name, doc_type):
    result, status_code = aggregations_with_keywords_and_filters(index_name, doc_type, request.args,
                                                                 request.args.getlist('aggregations'))

    if status_code == 200:
        return jsonify(meta=result['meta'],
                       aggregations=result['aggregations'],
                       links=result['links']), status_code
    else:
        return api_response(result, status_code)


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>',
            methods=['PUT'])
def index_document(index_name, doc_type, service_id):
    json_payload = get_json_from_request('service')
    mapping = app.mapping.get_mapping(index_name, doc_type)
    index_json = convert_request_json_into_index_json(mapping, json_payload)
    result, status_code = index(index_name, doc_type, index_json, service_id)

    return api_response(result, status_code)


@main.route('/<string:index_name>', methods=['PUT'])
def create(index_name):
    create_type = get_json_from_request('type')
    if create_type == 'index':
        mapping_name = get_json_from_request('mapping')
        result, status_code = create_index(index_name, mapping_name)
    elif create_type == 'alias':
        alias_target = get_json_from_request('target')
        result, status_code = create_alias(index_name, alias_target)
    else:
        abort(400, "Unrecognized 'type' value. Expected 'index' or 'alias'")

    return api_response(result, status_code)


@main.route('/<string:index_name>', methods=['DELETE'])
def delete(index_name):
    status, status_code = status_for_index(index_name)

    if status_code != 200:
        return api_response(status, status_code)

    if not status:
        return api_response("Cannot delete alias '{}'".format(index_name), 400)

    if status.get('aliases'):
        return api_response(
            "Index '{}' is aliased as '{}' and cannot be deleted".format(
                index_name, status['aliases'][0]
            ), 400)

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


@main.route('/<string:framework>/<string:object_type>/index', methods=['GET'])
def get_index_for_object_type(framework, object_type):
    try:
        index = current_app.config['DM_FRAMEWORK_TO_ES_INDEX_MAPPING'][framework][object_type]
    except KeyError:
        abort(400, "No index found for '{}' object type on '{}' framework".format(object_type, framework))

    return api_response(index, 200, 'index')


def api_response(data, status_code, key='message'):
    """Handle error codes.

    See http://elasticsearch-py.readthedocs.io/en/master/exceptions.html#elasticsearch.TransportError.status_code for
    an explaination of 'N/A' status code. elasticsearch-py client returns 'N/A' as status code if ES server cannot be
    reached
    """
    try:
        if status_code // 100 == 2:
            return jsonify({key: data}), status_code
    except TypeError as e:
        if status_code == 'N/A':
            return jsonify(error=str(data)), 500
        raise e
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
