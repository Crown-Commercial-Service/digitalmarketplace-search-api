from __future__ import absolute_import

import json

from werkzeug.datastructures import MultiDict

from app import create_app
from app import elasticsearch_client


def build_query_params(keywords=None, page=None, filters=None):
    query_params = MultiDict()
    if keywords:
        query_params["q"] = keywords
    if filters:
        for filter_raw_name, filter_value in filters.items():
            filter_name = "filter_{}".format(filter_raw_name)
            if isinstance(filter_value, list):
                for value in filter_value:
                    query_params.add(filter_name, value)
            else:
                query_params[filter_name] = filter_value
    if page:
        query_params["page"] = page
    return query_params


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
        self.default_mapping_name = "services"

        setup_authorization(self.app)

    def do_not_provide_access_token(self):
        self.app.wsgi_app = self.app.wsgi_app.app

    def create_index(self, index_name=None, expect_success=True):
        if index_name is None:
            index_name = self.default_index_name

        response = self.client.put('/{}'.format(index_name), data=json.dumps({
            "type": "index",
            "mapping": self.default_mapping_name,
        }), content_type="application/json")
        if expect_success:
            assert response.status_code in (200, 201)
        return response

    def teardown(self):
        with self.app.app_context():
            elasticsearch_client.indices.delete('index-*')


class BaseApplicationTestWithIndex(BaseApplicationTest):
    def setup(self):
        super().setup()
        self.create_index()


def setup_authorization(app):
    """Set up bearer token and pass on all requests"""
    app.wsgi_app = WSGIApplicationWithEnvironment(
        app.wsgi_app,
        HTTP_AUTHORIZATION='Bearer {}'.format(app.config['DM_SEARCH_API_AUTH_TOKENS']))


def make_standard_service(**kwargs):
    service = {
        "id": "id",
        "lot": "LoT",
        "serviceName": "serviceName",
        "serviceSummary": "serviceSummary",
        "serviceBenefits": "serviceBenefits",
        "serviceFeatures": "serviceFeatures",
        "serviceTypes": ["serviceTypes"],
        "supplierName": "Supplier Name",
        "minimumContractPeriod": "Month",
        "networksConnected": ["PSN", "PNN"],
        "datacentreTier": "tia-942 tier 1",
    }

    service.update(kwargs)

    return {
        "document": service
    }


def make_search_api_url(data, type_name='services'):
    # currently, data may contain either "document" or "service" (as a backward compatibility shim)
    return '/index-to-create/{}/{}'.format(type_name, str(data.get('document', data.get('service'))['id']))


def assert_response_status(response, expected_status):
    assert response.status_code == expected_status, "Expected {} response; got {}. {}".format(
        expected_status, response.status_code, response.get_data(as_text=True)
    )


def get_json_from_response(response):
    return json.loads(response.get_data())
