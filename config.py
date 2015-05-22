import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    AUTH_REQUIRED = True
    ALLOW_EXPLORER = True
    DM_SEARCH_PAGE_SIZE = 100
    # Logging
    DM_LOG_LEVEL = 'DEBUG'
    DM_APP_NAME = 'search-api'
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'
    DM_REQUEST_ID_HEADER = 'DM-Request-ID'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Amz-Cf-Id'

    @staticmethod
    def init_app(app):
        pass


class Test(Config):
    DEBUG = True
    DM_LOG_LEVEL = 'CRITICAL'


class Development(Config):
    DEBUG = True
    DM_SEARCH_PAGE_SIZE = 5


class Live(Config):
    DEBUG = False
    ALLOW_EXPLORER = False


config = {
    'development': Development,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Test,
}
