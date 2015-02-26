# digitalmarketplace-search-api
API to handle interactions between the digitalmarketplace applications and search applications.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Setup

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

Create a virtual environment
 
 ```
virtualenv ./venv
 ```
 
Ensure you have Elasticsearch running locally


### Activate the virtual environment

```
source ./venv/bin/activate
```

### Upgrade dependencies

Install new Python dependencies with pip

```pip install -r requirements_for_test.txt```

### Run the tests

```
./scripts/run_tests.sh
```

### Run the development server

```
python application.py runserver
```

### Using the API locally

Calls to the API require a valid bearer token. Tokens to be accepted can be set using the AUTH_TOKENS environment variable, e.g.:

```export AUTH_TOKENS=myToken```

and then you can include this token in your request headers, e.g.:

```
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5000/search
```
