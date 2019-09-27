from flask import Flask
import json
from config import config as configs
from flask_elasticsearch import FlaskElasticsearch

from dmutils.flask import DMGzipMiddleware
from dmutils.flask_init import init_app, api_error_handlers

elasticsearch_client = FlaskElasticsearch()


def get_service_by_name_from_vcap_services(vcap_services, name):
    """Returns the first service from a VCAP_SERVICES json object that has name"""
    for services in vcap_services.values():
        for service in services:
            if service['name'] == name:
                return service

    raise RuntimeError(f"Unable to find service with name {name} in VCAP_SERVICES")


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        error_handlers=api_error_handlers,
    )

    if application.config['VCAP_SERVICES']:
        cf_services = json.loads(application.config['VCAP_SERVICES'])
        service = get_service_by_name_from_vcap_services(
            cf_services, application.config['DM_ELASTICSEARCH_SERVICE_NAME'])

        application.config['ELASTICSEARCH_HOST'] = service['credentials']['uri']

    elasticsearch_client.init_app(
        application,
        verify_certs=True,
    )

    from .metrics import metrics as metrics_blueprint, gds_metrics
    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(metrics_blueprint)
    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)

    gds_metrics.init_app(application)

    # because the search api doesn't return any values in its bodies we would consider "secrets", we should be
    # able to safely gzip all response bodies without concerns about BREACH et al.
    DMGzipMiddleware(application, compress_by_default=True)

    return application
