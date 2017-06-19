from flask import Flask
from config import config as configs
from flask.ext.elasticsearch import FlaskElasticsearch
from dmutils import init_app, flask_featureflags

feature_flags = flask_featureflags.FeatureFlag()
elasticsearch_client = FlaskElasticsearch()


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        feature_flags=feature_flags
    )

    elasticsearch_client.init_app(
        application,
        verify_certs=True
    )

    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)

    return application
