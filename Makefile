SHELL := /bin/bash
VIRTUALENV_ROOT := $(shell [ -z $$VIRTUAL_ENV ] && echo $$(pwd)/venv || echo $$VIRTUAL_ENV)

.PHONY: run-all
run-all: requirements run-app

.PHONY: run-app
run-app: virtualenv
	${VIRTUALENV_ROOT}/bin/flask run

.PHONY: virtualenv
virtualenv:
	[ -z $$VIRTUAL_ENV ] && [ ! -d venv ] && python3 -m venv venv || true

.PHONY: requirements
requirements: virtualenv test-requirements requirements.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements.txt

.PHONY: requirements-dev
requirements-dev: virtualenv requirements-dev.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements-dev.txt

.PHONY: freeze-requirements
freeze-requirements: virtualenv requirements-dev requirements-app.txt
	${VIRTUALENV_ROOT}/bin/python -m dmutils.repoutils.freeze_requirements requirements-app.txt

.PHONY: test
test: test-requirements test-flake8 test-unit

.PHONY: test-requirements
test-requirements:
	@diff requirements-app.txt requirements.txt | grep '<' \
	    && { echo "requirements.txt doesn't match requirements-app.txt."; \
	         echo "Run 'make freeze-requirements' to update."; exit 1; } \
	    || { echo "requirements.txt is up to date"; exit 0; }

.PHONY: test-flake8
test-flake8: virtualenv requirements-dev
	${VIRTUALENV_ROOT}/bin/flake8 .

.PHONY: test-unit
test-unit: virtualenv requirements-dev
	${VIRTUALENV_ROOT}/bin/py.test ${PYTEST_ARGS}

.PHONY: docker-build
docker-build:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	@echo "Building a docker image for ${RELEASE_NAME}..."
	docker build -t digitalmarketplace/search-api --build-arg release_name=${RELEASE_NAME} .
	docker tag digitalmarketplace/search-api digitalmarketplace/search-api:${RELEASE_NAME}

.PHONY: docker-push
docker-push:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	docker push digitalmarketplace/search-api:${RELEASE_NAME}
