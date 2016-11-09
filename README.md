# digitalmarketplace-search-api
API to handle interactions between the digitalmarketplace applications and search.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Quickstart

Install [elasticsearch](http://www.elasticsearch.org/). This must be in the 1.x series not the 2.x series.
```
brew update
brew install homebrew/versions/elasticsearch17
```

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)
```
sudo easy_install virtualenv
```

Install dependencies and run the app
```
make run_all
```

## Setup

Install [elasticsearch](http://www.elasticsearch.org/). This must be in the 1.x series not the 2.x series.

```
brew update
brew install homebrew/versions/elasticsearch17
```

**Debian users** might have to use elasticsearch 1.6 available in `jessie-backports` and uncomment `START_DAEMON=true` in `/etc/default/elasticsearch` before starting elasticsearch using `systemctl start elasticsearch`.

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

Create a virtual environment in the checked-out repository folder

```
make virtualenv
```

### Activate the virtual environment

```
source ./venv/bin/activate
```

### Upgrade dependencies

Install Python dependencies with pip

```
make requirements_for_test
```

### Insert G6 services into elasticsearch index

Start elasticsearch (in a new console window/tab)

```
elasticsearch
```

The process for indexing of services is changing and this documentation will be updated shortly. In the meantime the explorer (see below) can be used to insert documents.


Set the required environment variable (in production this will point to the
load balancer in front of the Elasticsearch cluster).

```
export DM_ELASTICSEARCH_URL=http://localhost:9200
```

### Run the tests

```
make test
```

### Run the development server

To run the Search API for local development you can use the convenient run
script, which sets the required environment variables for local development:
```
make run_app
```

More generally, the command to start the server is:
```
python application.py runserver
```

### Using the Search API locally

The Search API runs on port 5001. Calls to the API require a valid bearer
token. Tokens to be accepted can be set using the DM_SEARCH_API_AUTH_TOKENS
environment variable, e.g.:

```export DM_SEARCH_API_AUTH_TOKENS=myToken```

and then you can include this token in your request headers, e.g.:

```
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5001/g-cloud/services/search?q=email
```

Alternatively there is an API explorer running on

    [http://localhost:5001/_explorer](http://localhost:5001/_explorer)

Which provides a UI over the API calls.

### Using FeatureFlags

To use feature flags, check out the documentation in (the README of)
[digitalmarketplace-utils](https://github.com/alphagov/digitalmarketplace-utils#using-featureflags).

### Updating the index mapping

Whenever the mappings JSON file is updated, a new version value should be written to the mapping
metadata in `"_meta": {"version": VALUE}`.

Mapping can be updated by issuing a PUT request to the existing index enpoint:

```
PUT /g-cloud-index HTTP/1.1
Authorization: Bearer myToken
Content-Type: application/json

{"type": "index"}
```

If the mapping cannot be updated in-place, [zero-downtime mapping update process](https://www.elastic.co/blog/changing-mapping-with-zero-downtime) should be used instead:

1. Create a new index, using the `index-name-YYYY-MM-DD` pattern for the new index name.
   ```
   PUT /g-cloud-2015-09-29 HTTP/1.1
   Authorization: Bearer myToken
   Content-Type: application/json

   {"type": "index"}
   ```
2. Reindex documents into the new index using existing index document endpoints with the new index name
3. Once the indexing is finished, update the index alias to point to the new index:
   ```
   PUT /g-cloud HTTP/1.1
   Authorization: Bearer myToken
   Content-Type: application/json

   {"type": "alias", "target": "g-cloud-2015-09-29"}
   ```

4. Once the alias is updated the old index can be removed:
   ```
   DELETE /g-cloud-index HTTP/1.1
   Authorization: Bearer myToken
   ```
