from flask import request

from . import status
from ..main.services.search_service import status_for_all_indexes
from dmutils.status import get_app_status, StatusError


def get_es_status():
    result, status_code = status_for_all_indexes()

    if status_code != 200:
        raise StatusError(f'Error connecting to elasticsearch (status_code: {status_code}, message: {result})')

    return {
        'es_status': result
    }


@status.route('/_status')
def status():
    return get_app_status(data_api_client=None,
                          search_api_client=None,
                          ignore_dependencies='ignore-dependencies' in request.args,
                          additional_checks=[get_es_status])
