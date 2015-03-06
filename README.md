# digitalmarketplace-search-api
API to handle interactions between the digitalmarketplace applications and search applications.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Setup

Install [elasticsearch](http://www.elasticsearch.org/)

```
brew update
brew install elasticsearch
```

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

Create a virtual environment in the checked-out repository folder
 
 ```
cd digitalmarketplace-search-api
virtualenv ./venv
 ```

### Activate the virtual environment

```
source ./venv/bin/activate
```

### Upgrade dependencies

Install Python dependencies with pip

```pip install -r requirements_for_test.txt```

### Insert G6 services into elasticsearch index

Start elasticsearch (in a new console window/tab)

```
elasticsearch
```

Index G6 services into your local elasticsearch index:

```
./scripts/index-g6-in-elasticsearch.py http://localhost:9200/services https://api.digitalmarketplace.service.gov.uk/services <api_bearer_token>
```

Set the required environment variable (in production this will point to the 
load balancer in front of the Elasticsearch cluster).

```
export DM_ELASTICSEARCH_URL=http://localhost:9200
```

### Run the tests

```
./scripts/run_tests.sh
```

### Run the development server

To run the Search API for local development you can use the convenient run 
script, which sets the required environment variables for local development: 
```
./scripts/run_app.sh
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
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5001/search?q=email
```
