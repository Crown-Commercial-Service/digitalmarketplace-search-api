from flask import Flask
import base64
import json
from config import config as configs
from flask.ext.elasticsearch import FlaskElasticsearch
from dmutils import init_app, flask_featureflags

feature_flags = flask_featureflags.FeatureFlag()
elasticsearch_client = FlaskElasticsearch()


def get_service_by_tag_from_vcap_services(vcap_services, tag):
    """Returns the first service from a VCAP_SERVICES json object that has tag"""
    for services in vcap_services.values():
        for service in services:
            if tag in service['tags']:
                return service

    raise RuntimeError(f"Unable to find service with tag(s) {tag} in VCAP_SERVICES")


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        feature_flags=feature_flags
    )

    if application.config['VCAP_SERVICES']:
        cf_services = json.loads(application.config['VCAP_SERVICES'])
        service = get_service_by_tag_from_vcap_services(cf_services, 'elasticsearch')

        application.config['ELASTICSEARCH_HOST'] = \
            service['credentials']['uris']

        with open(application.config['DM_ELASTICSEARCH_CERT_PATH'], 'wb') as es_certfile:
            es_certfile.write(
                base64.b64decode(service['credentials']['ca_certificate_base64'])
            )

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
