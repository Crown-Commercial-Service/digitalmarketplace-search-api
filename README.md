# Digital Marketplace Search API

![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)

API application for Digital Marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

This app handles interactions between the Digital Marketplace apps and our Elasticsearch instance.

## Quickstart

It's recommended to use the [DM Runner](https://github.com/Crown-Commercial-Service/digitalmarketplace-runner)
tool, which will install and run the app (and an Elasticsearch instance) as part of the full suite of apps.

If you want to run the app as a stand-alone process, you'll need to set the `ELASTICSEARCH_HOST` env variable
to your own local ES instance.

You can then clone the repo and run:

```
make run-all
```

This command will install dependencies and start the app.

By default, the app will be served at [http://127.0.0.1:5009](http://127.0.0.1:5009).

### Local Elasticsearch setup
Install version 6.x of [elasticsearch](http://www.elasticsearch.org/), ideally 6.8 which is what we run on live systems.

```
brew update
brew install elasticsearch@6.8
```

Start elasticsearch via brew:

```bash
brew services start elasticsearch
```

See the [Developer Manual](https://crown-commercial-service.github.io/digitalmarketplace-manual/developing-the-digital-marketplace/developer-setup.html)
for more details around local developer setup.

## Using the Search API

Calls to the Search API require a valid bearer token. For development
environments, this defaults to `myToken`. An example request to your local
search API would therefore be:

```
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5009/g-cloud/services/search?q=email
```

POST requests will require a `Content-Type` header, set to `application/json`.

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

[frameworks repository]: https://github.com/Crown-Commercial-Service/digitalmarketplace-frameworks
[`generate-search-config.py`]: https://github.com/Crown-Commercial-Service/digitalmarketplace-frameworks/blob/main/scripts/generate-search-config.py

### Indexing data

On preview, staging and production, the overnight Jenkins jobs do not create new indices, but instead
overwrite whichever index the alias currently points to.

New indices are only created and aliased if the entire data set needs to be reindexed, e.g. following a
database reset or a change in the mapping. This is done with two scripts for each framework:

1. [index-to-search-service.py](https://github.com/Crown-Commercial-Service/digitalmarketplace-scripts/blob/main/scripts/index-to-search-service.py)

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
2. [update-index-alias.py](https://github.com/Crown-Commercial-Service/digitalmarketplace-scripts/blob/main/scripts/update-index-alias.py)

   Update the alias to point to the new index (that has the date suffix):

   ```
   ./scripts/update-index-alias.py g-cloud-9 g-cloud-9-2018-01-01 <search-api-url>
   ./scripts/update-index-alias.py briefs-digital-outcomes-and-specialists briefs-digital-outcomes-and-specialists-2018-01-01 <search-api-url>
   ```

   This script also deletes the old index.

## Testing

Run the full test suite:

```
make test
```

To only run the Python tests:

```
make test-unit
```

To run the `flake8` linter:

```
make test-flake8
```

### Updating Python dependencies

`requirements.txt` file is generated from the `requirements.in` in order to pin
versions of all nested dependencies. If `requirements.in` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be committed alongside `requirements.in` changes.

## Contributing

This repository is maintained by the Digital Marketplace team at the [Crown Commercial Service](https://github.com/Crown-Commercial-Service).

If you have a suggestion for improvement, please raise an issue on this repo.

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
