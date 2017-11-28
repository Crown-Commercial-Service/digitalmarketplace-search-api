from flask import jsonify, request

from app.main import main
from app.main.services.response_formatters import api_response
from app.main.services.search_service import search_with_keywords_and_filters, aggregations_with_keywords_and_filters, \
    fetch_by_id


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
            methods=['GET'])
def fetch_service(index_name, doc_type, service_id):
    result, status_code = fetch_by_id(index_name, doc_type, service_id)

    if status_code == 200:
        return jsonify(services=result), status_code
    else:
        return api_response(result, status_code)
