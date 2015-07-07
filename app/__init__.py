from flask import Flask
from config import config as configs
from flask.ext.bootstrap import Bootstrap
from flask.ext.elasticsearch import FlaskElasticsearch
from dmutils import init_app, flask_featureflags

bootstrap = Bootstrap()
feature_flags = flask_featureflags.FeatureFlag()
elasticsearch_client = FlaskElasticsearch()


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        bootstrap=bootstrap,
        feature_flags=feature_flags
    )

    elasticsearch_client.init_app(application)

    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)
    if configs[config_name].ALLOW_EXPLORER:
        from .explorer import explorer as explorer_blueprint

        application.register_blueprint(explorer_blueprint)
    return application
