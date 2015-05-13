from flask import jsonify, current_app

from . import status
from . import utils
from ..main.services.search_service import status_for_all_indexes


@status.route('/_status')
def status():
    result, status_code = status_for_all_indexes()

    if status_code == 200:
        return jsonify(
            status="ok",
            version=utils.get_version_label(),
            es_status=result,
        )

    current_app.logger.exception("Error connecting to elasticsearch")

    return jsonify(
        status="error",
        version=utils.get_version_label(),
        message="Error connecting to elasticsearch",
        es_status={
            'status_code': status_code,
            'message': "{}".format(result),
        }
    ), 500
