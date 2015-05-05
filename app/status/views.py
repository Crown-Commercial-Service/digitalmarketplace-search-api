from flask import jsonify, current_app

from . import status
from . import utils
from ..main.services.search_service import status_for_all_indexes


@status.route('/_status')
def status():

    db_status = status_for_all_indexes()

    if db_status['status_code'] == 200:
        return jsonify(
            status="ok",
            version=utils.get_version_label(),
            db_status=db_status
        )

    current_app.logger.exception("Error connecting to elasticsearch")

    return jsonify(
        status="error",
        version=utils.get_version_label(),
        message="Error connecting to elasticsearch",
        db_status={
            'status_code': 500,
            'message': db_status['message'][0]
        }
    ), 500
