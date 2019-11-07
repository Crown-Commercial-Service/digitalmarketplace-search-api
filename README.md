# digitalmarketplace-search-api

[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-search-api/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-search-api/requirements/?branch=master)
![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)

API to handle interactions between the digitalmarketplace applications and search.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Quickstart

Install [elasticsearch](http://www.elasticsearch.org/). This must be in the 5.x series; ideally 5.6 which is what we run on live systems.
```
brew update
brew cask install java
cd /usr/local/Homebrew/Library/Taps/homebrew/homebrew-core
git fetch --unshallow
git checkout 3f9a5fc50e42f6bdd17f955419c299653a0f65b9 Formula/elasticsearch.rb # (version: 5.6.4)
HOMEBREW_NO_AUTO_UPDATE=1 brew install elasticsearch
git reset --hard master
```

### Install/Upgrade dependencies

Install Python dependencies with pip

```
make requirements-dev
```

### Run the tests

```
make test
```

### Run the development server

To run the Search API for local development you can use the convenient run
script, which sets the required environment variables for local development:
```
make run-app
```

More generally, the command to start the development server is:
```
DM_ENVIRONMENT=development flask run
```

### Using the Search API locally

Start elasticsearch if not already running via brew (in a new console window/tab):

```bash
brew services start elasticsearch
< OR >
elasticsearch
```

Calls to the Search API require a valid bearer token. For development
environments, this defaults to `myToken`. An example request to your local
search API would therefore be:

```
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5009/g-cloud/services/search?q=email
```

When running the Search API locally it listens on port 5009 by default. This can
be changed by setting the `DM_SEARCH_API_PORT` environment variable, e.g. to set
the search api port number to 9001:

```
export DM_SEARCH_API_PORT=9001
```

### Updating application dependencies

`requirements.txt` file is generated from the `requirements-app.txt` in order to pin
versions of all nested dependecies. If `requirements-app.txt` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be committed alongside `requirements-app.txt` changes.

### Updating the index mapping

The index mapping is generated using the [`generate-search-config.py`] script
from the framework question content and mapping templates in the [frameworks repository].

For example, to (re-)generate the services mapping for G-cloud 10, you could run

    digitalmarketplace-frameworks/scripts/generate-search-config.py g-cloud-10 services > digitalmarketplace-search-api/mappings/g-cloud-10-services.json

Once this has been done the mapping file will need to be committed and the
commit released. You can then tell Elasticsearch to use the new mapping.

To use the new mapping you will need to create a new index, it will not be
picked up automatically. You can either do this manually by following the steps
[below](#indexing-data), or by using the jobs on Jenkins.

[frameworks repository]: https://github.com/alphagov/digitalmarketplace-frameworks/
[`generate-search-config.py`]: https://github.com/alphagov/digitalmarketplace-frameworks/blob/master/scripts/generate-search-config.py

### Indexing data

On preview, staging and production, the overnight Jenkins jobs do not create new indices, but instead
overwrite whichever index the alias currently points to.

New indices are only created and aliased if the entire data set needs to be reindexed, e.g. following a
database reset or a change in the mapping. This is done with two scripts for each framework:

1. [index-to-search-service.py](https://github.com/alphagov/digitalmarketplace-scripts/blob/master/scripts/index-to-search-service.py)

   Create a new index, using the `index-name-YYYY-MM-DD` pattern for the new index name.

   ```
   ./scripts/index-to-search-service.py services dev
                                        --index=g-cloud-9-2018-01-01
                                        --frameworks=g-cloud-9
                                        --create-with-mapping=services
   ./scripts/index-to-search-service.py briefs dev
                                        --index=briefs-digital-outcomes-and-specialists-2018-01-01
                                        --frameworks=digital-outcomes-and-specialists
                                        --create-with-mapping=briefs-digital-outcomes-and-specialists-2
   ```
2. [update-index-alias.py](https://github.com/alphagov/digitalmarketplace-scripts/blob/master/scripts/update-index-alias.py)

   Update the alias to point to the new index (that has the date suffix):

   ```
   ./scripts/update-index-alias.py g-cloud-9 g-cloud-9-2018-01-01 <search-api-url>
   ./scripts/update-index-alias.py briefs-digital-outcomes-and-specialists briefs-digital-outcomes-and-specialists-2018-01-01 <search-api-url>
   ```

   This script also deletes the old index.
