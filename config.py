import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    AUTH_REQUIRED = True
    ALLOW_EXPLORER = True

    @staticmethod
    def init_app(app):
        pass


class Test(Config):
    DEBUG = True


class Development(Config):
    DEBUG = True


class Live(Config):
    DEBUG = False
    ALLOW_EXPLORER = False


config = {
    'development': Development,
    'preview': Development,
    'staging': Live,
    'production': Live,
    'test': Test,
}
