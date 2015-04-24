from flask import Flask
from config import config
from flask.ext.bootstrap import Bootstrap
from dmutils import logging

from .main import main as main_blueprint
from .status import status as status_blueprint


bootstrap = Bootstrap()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    logging.init_app(app)

    app.register_blueprint(status_blueprint)
    app.register_blueprint(main_blueprint)
    if config[config_name].ALLOW_EXPLORER:
        from .explorer import explorer as explorer_blueprint

        app.register_blueprint(explorer_blueprint)
    return app
