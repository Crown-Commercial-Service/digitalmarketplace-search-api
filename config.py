import os
from dmutils.status import get_version_label

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    AUTH_REQUIRED = True

    ELASTICSEARCH_HOST = 'localhost:9200'

    DM_ELASTICSEARCH_CERT_PATH = None

    DM_SEARCH_API_AUTH_TOKENS = None
    DM_FRAMEWORK_TO_ES_INDEX_MAPPING = {
        'g-cloud-9': {
            'services': 'g-cloud-9'
        },
        'digital-outcomes-and-specialists-2': {
            'briefs': 'briefs-digital-outcomes-and-specialists-2'
        }
    }

    DM_SEARCH_PAGE_SIZE = 100
    DM_ID_ONLY_SEARCH_PAGE_SIZE_MULTIPLIER = 10
    # Logging
    DM_LOG_LEVEL = 'DEBUG'
    DM_APP_NAME = 'search-api'
    DM_PLAIN_TEXT_LOGS = False
    DM_LOG_PATH = None
    DM_REQUEST_ID_HEADER = 'DM-Request-ID'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Amz-Cf-Id'

    # Feature Flags
    RAISE_ERROR_ON_MISSING_FEATURES = True

    VCAP_SERVICES = None

    @staticmethod
    def init_app(app):
        pass


class Test(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    DM_LOG_LEVEL = 'CRITICAL'

    DM_SEARCH_API_AUTH_TOKENS = 'valid-token'


class Development(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    DM_SEARCH_PAGE_SIZE = 5

    DM_SEARCH_API_AUTH_TOKENS = 'myToken'


class Live(Config):
    DEBUG = False

    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'
    DM_ELASTICSEARCH_CERT_PATH = '/tmp/elasticsearch-certificate'


config = {
    'development': Development,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Test,
}
