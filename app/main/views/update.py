from flask import request
from werkzeug.exceptions import abort

from app.main import main
from app.mapping import get_mapping
from app.main.services.process_request_json import convert_request_json_into_index_json, check_json_from_request
from app.main.services.response_formatters import api_response
from app.main.services.search_service import index, delete_by_id


@main.route('/<string:index_name>/<string:doc_type>/<string:document_id>', methods=['PUT'])
def index_document(index_name, doc_type, document_id):
    payload = check_json_from_request(request)
    json_payload = payload.get('document') or payload.get('service')  # fallback to 'service' for backward-compat.
    if json_payload is None:
        abort(400, "Invalid JSON must have 'document' key.")

    mapping = get_mapping(index_name, doc_type)
    index_json = convert_request_json_into_index_json(mapping, json_payload)
    result, status_code = index(index_name, doc_type, index_json, document_id)

    return api_response(result, status_code)


@main.route('/<string:index_name>/<string:doc_type>/<string:service_id>', methods=['DELETE'])
def delete_service(index_name, doc_type, service_id):
    # This checks that the index_name and doc_type exist or 400s
    get_mapping(index_name, doc_type)

    result, status_code = delete_by_id(index_name, doc_type, service_id)

    return api_response(result, status_code)
