from werkzeug.exceptions import abort

from app.main import main
from app.main.services.search_service import create_index, create_alias, status_for_index, delete_index
from app.main.services.process_request_json import get_json_from_request
from app.main.services.response_formatters import api_response


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
