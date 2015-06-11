from flask import Flask
from config import config as configs
from flask.ext.bootstrap import Bootstrap
from dmutils import init_app, flask_featureflags

from .main import main as main_blueprint
from .status import status as status_blueprint


bootstrap = Bootstrap()
feature_flags = flask_featureflags.FeatureFlag()


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        bootstrap=bootstrap,
        feature_flags=feature_flags
    )

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)
    if configs[config_name].ALLOW_EXPLORER:
        from .explorer import explorer as explorer_blueprint

        application.register_blueprint(explorer_blueprint)
    return application
