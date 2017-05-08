SHELL := /bin/bash
VIRTUALENV_ROOT := $(shell [ -z $$VIRTUAL_ENV ] && echo $$(pwd)/venv || echo $$VIRTUAL_ENV)

run_all: requirements run_app

run_app: virtualenv
	${VIRTUALENV_ROOT}/bin/python application.py runserver

virtualenv:
	[ -z $$VIRTUAL_ENV ] && [ ! -d venv ] && virtualenv venv || true

requirements: virtualenv requirements.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements.txt

requirements_for_test: virtualenv requirements_for_test.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements_for_test.txt

test: test_pep8 test_unit

test_pep8: virtualenv
	${VIRTUALENV_ROOT}/bin/pep8 .

test_unit: virtualenv
	${VIRTUALENV_ROOT}/bin/py.test ${PYTEST_ARGS}

docker-build:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	@echo "Building a docker image for ${RELEASE_NAME}..."
	docker build --pull -t digitalmarketplace/search-api --build-arg release_name=${RELEASE_NAME} .
	docker tag digitalmarketplace/search-api digitalmarketplace/search-api:${RELEASE_NAME}

docker-push:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	docker push digitalmarketplace/search-api:${RELEASE_NAME}

.PHONY: virtualenv requirements requirements_for_test test_pep8 test_unit test run_app run_all docker-build docker-push
