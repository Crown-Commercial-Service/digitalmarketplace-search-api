from flask import jsonify, current_app

from . import status
from . import utils
from ..main.services.search_service import status_for_all_indexes


@status.route('/_status')
def status():

    es_status = status_for_all_indexes()

    if es_status['status_code'] == 200:
        return jsonify(
            status="ok",
            version=utils.get_version_label(),
            es_status=es_status
        )

    current_app.logger.exception("Error connecting to elasticsearch")

    return jsonify(
        status="error",
        version=utils.get_version_label(),
        message="Error connecting to elasticsearch",
        es_status={
            'status_code': es_status['status_code'],
            'message': "{}".format(es_status['message'])
        }
    ), 500
