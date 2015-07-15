from flask import jsonify, current_app, request

from . import status
from ..main.services.search_service import status_for_all_indexes
from dmutils.status import get_flags


@status.route('/_status')
def status():

    if 'ignore-dependencies' in request.args:
        return jsonify(
            status="ok",
        ), 200

    result, status_code = status_for_all_indexes()
    version = current_app.config['VERSION']

    if status_code == 200:
        return jsonify(
            status="ok",
            version=version,
            es_status=result,
            flags=get_flags(current_app)
        )

    current_app.logger.exception("Error connecting to elasticsearch")

    return jsonify(
        status="error",
        version=version,
        message="Error connecting to elasticsearch",
        es_status={
            'status_code': status_code,
            'message': "{}".format(result),
        },
        flags=get_flags(current_app)
    ), 500
