
from app import get_service_by_name_from_vcap_services

import pytest


@pytest.fixture
def elasticsearch_compose():
    return {
        "elasticsearch-compose": [{
            "instance_name": "search_api_elasticsearch",
            "label": "elasticsearch-compose",
            "name": "search_api_elasticsearch",
            "tags": [
                "elasticsearch",
                "compose",
            ],
        }]
    }


@pytest.fixture
def elasticsearch():
    return {
        "elasticsearch": [{
            "instance_name": "search_api_elasticsearch",
            "label": "elasticsearch",
            "name": "search_api_elasticsearch",
            "tags": [
                "elasticsearch",
            ],
        }]
    }


@pytest.fixture
def multiple_services(elasticsearch, elasticsearch_compose):
    return {**elasticsearch, **elasticsearch_compose}


def test_get_service_by_name_finds_elasticsearch_compose(elasticsearch_compose):
    service = get_service_by_name_from_vcap_services(elasticsearch_compose, 'search_api_elasticsearch')
    assert service == elasticsearch_compose['elasticsearch-compose'][0]


def test_get_service_by_name_raises_runtime_error_if_it_cannot_find_the_service(elasticsearch_compose):
    with pytest.raises(RuntimeError):
        get_service_by_name_from_vcap_services(elasticsearch_compose, 'garbage')


def test_get_service_by_name_finds_first_service_with_name(multiple_services):
    service = get_service_by_name_from_vcap_services(multiple_services, 'search_api_elasticsearch')
    assert service == multiple_services['elasticsearch'][0]
