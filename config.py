import os
from dmutils.status import get_version_label

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    AUTH_REQUIRED = True

    ELASTICSEARCH_HOST = 'localhost:9200'

    DM_SEARCH_API_AUTH_TOKENS = None

    DM_SEARCH_PAGE_SIZE = 30
    DM_ID_ONLY_SEARCH_PAGE_SIZE_MULTIPLIER = 10
    # Logging
    DM_LOG_LEVEL = 'DEBUG'
    DM_APP_NAME = 'search-api'
    DM_PLAIN_TEXT_LOGS = False
    DM_LOG_PATH = None

    VCAP_SERVICES = None
    DM_ELASTICSEARCH_SERVICE_NAME = "search_api_elasticsearch"

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

    DM_SEARCH_API_AUTH_TOKENS = 'myToken'


class NativeAWS(Config):
    DEBUG = False
    DM_APP_NAME = 'search-api'
    DM_HTTP_PROTO = 'https'

class Live(Config):
    DEBUG = False

    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'


config = {
    'development': Development,
    'native-aws': NativeAWS,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Test,
}
