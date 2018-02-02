from flask import Flask
import base64
import json
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

    if application.config['VCAP_SERVICES']:
        cf_services = json.loads(application.config['VCAP_SERVICES'])
        application.config['ELASTICSEARCH_HOST'] = cf_services['elasticsearch'][0]['credentials']['uris']

        with open(application.config['DM_ELASTICSEARCH_CERT_PATH'], 'wb') as es_certfile:
            es_certfile.write(base64.b64decode(cf_services['elasticsearch'][0]['credentials']['ca_certificate_base64']))

    elasticsearch_client.init_app(
        application,
        verify_certs=True,
        ca_certs=application.config['DM_ELASTICSEARCH_CERT_PATH']
    )

    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)

    return application
