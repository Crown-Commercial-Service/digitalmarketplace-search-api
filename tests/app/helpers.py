from __future__ import absolute_import

import os

from app import create_app


class WSGIApplicationWithEnvironment(object):
    def __init__(self, app, **kwargs):
        self.app = app
        self.kwargs = kwargs

    def __call__(self, environ, start_response):
        for key, value in self.kwargs.items():
            environ[key] = value
        return self.app(environ, start_response)


class BaseApplicationTest(object):

    def setup(self):
        self.app = create_app('test')
        self.client = self.app.test_client()
        self.default_index_name = "index-to-create"

        setup_authorization(self.app)

    def do_not_provide_access_token(self):
        self.app.wsgi_app = self.app.wsgi_app.app

    def teardown(self):
        self.client.delete('/' + self.default_index_name)
        teardown_authorization()


def setup_authorization(app):
    """Set up bearer token and pass on all requests"""
    valid_token = 'valid-token'
    app.wsgi_app = WSGIApplicationWithEnvironment(
        app.wsgi_app,
        HTTP_AUTHORIZATION='Bearer {}'.format(valid_token))
    os.environ['DM_SEARCH_API_AUTH_TOKENS'] = valid_token


def teardown_authorization():
    del os.environ['DM_SEARCH_API_AUTH_TOKENS']


def default_service(**kwargs):
    service = {
        "id": "id",
        "lot": "LoT",
        "serviceName": "serviceName",
        "serviceSummary": "serviceSummary",
        "serviceBenefits": "serviceBenefits",
        "serviceFeatures": "serviceFeatures",
        "serviceTypes": ["serviceTypes"],
        "supplierName": "Supplier Name",
        "freeOption": True,
        "trialOption": True,
        "minimumContractPeriod": "Month",
        "supportForThirdParties": True,
        "selfServiceProvisioning": True,
        "datacentresEUCode": True,
        "dataBackupRecovery": True,
        "dataExtractionRemoval": True,
        "networksConnected": ["PSN", "PNN"],
        "datacentreTier": "tia-942 tier 1",
        "apiAccess": True,
        "openStandardsSupported": True,
        "openSource": True,
        "persistentStorage": True,
        "guaranteedResources": True,
        "elasticCloud": True
    }

    service.update(kwargs)

    return {
        "service": service
    }
