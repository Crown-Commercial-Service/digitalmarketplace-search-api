from flask import jsonify, current_app

from . import status
from ..main.services.search_service import status_for_all_indexes
from dmutils.status import get_version_label, get_flags


@status.route('/_status')
def status():
    result, status_code = status_for_all_indexes()

    if status_code == 200:
        return jsonify(
            status="ok",
            version=get_version_label(),
            es_status=result,
            flags=get_flags(current_app)
        )

    current_app.logger.exception("Error connecting to elasticsearch")

    return jsonify(
        status="error",
        version=get_version_label(),
        message="Error connecting to elasticsearch",
        es_status={
            'status_code': status_code,
            'message': "{}".format(result),
        },
        flags=get_flags(current_app)
    ), 500
