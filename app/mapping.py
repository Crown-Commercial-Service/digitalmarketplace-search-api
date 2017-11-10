import os.path
from functools import reduce
from itertools import groupby
from operator import or_

from flask import json
from werkzeug.exceptions import BadRequest
from app import elasticsearch_client as es


SERVICES_MAPPING_FILE_SPEC = "mappings/services.json"
SERVICE_ID_HASH_FIELD_NAME = "serviceIdHash"

_mapping_files = None  # dict(name: filespec)


class MappingNotFound(BadRequest):
    pass


class Mapping(object):
    filter_field_prefix = "dmfilter"
    text_search_field_prefix = "dmtext"
    sort_only_field_prefix = "dmsortonly"
    aggregatable_field_prefix = "dmagg"

    # for now, these definitions are identical
    response_field_prefix = "dmtext"

    def __init__(self, mapping_definition, mapping_type):
        self.definition = mapping_definition
        properties = self.definition['mappings'][mapping_type]['properties']

        # build a dict of {prefix: frozenset(unprefixed_field_names)}
        self.fields_by_prefix = {
            prefix: frozenset(name for _, name in pairs)
            for prefix, pairs in groupby(
                (
                    (prefix, maybe_name_seq[0])
                    for prefix, *maybe_name_seq in (
                        full_field_name.split("_", 1)
                        for full_field_name in sorted(properties.keys())
                    )
                    if maybe_name_seq  # maybe_name_seq would be an empty seq if no underscores were found, discard them
                ),
                key=lambda x: x[0],  # (the prefix)
            )
        }
        # now generate the inverse, {field_name: frozenset(prefixes)}
        self.prefixes_by_field = {
            name: frozenset(prefix for prefix, names in self.fields_by_prefix.items() if name in names)
            for name in reduce(or_, self.fields_by_prefix.values() or frozenset())
        }

        self.transform_fields = tuple(
            self.definition['mappings'][mapping_type].get('_meta', {}).get('transformations', {})
        )


def get_mapping(index_name, document_type):
    # es.indices.get_mapping has a key for the index name, regardless of any alias we may be going via, so rather than
    # use index_name, we access the one and only value in the dictionary using next(iter).
    mapping_data = next(iter(es.indices.get_mapping(index=index_name, doc_type=document_type).values()))

    # In ES <=5, there may be multiple mapping types per document type (kind-of) - this is confusing, but going away,
    # see <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/removal-of-types.html>. For us, document_type
    # === mapping_type, and there will be only one per index.
    return Mapping(mapping_data, mapping_type=document_type)


def load_mapping_definition(mapping_name):
    mapping_file_spec = get_mapping_file_paths_by_name().get(mapping_name)
    if mapping_file_spec is not None:
        with open(mapping_file_spec) as mapping_file:
            return json.load(mapping_file)

    else:
        raise MappingNotFound("Mapping definition named '{}' not found.".format(mapping_name))


def get_mapping_file_paths_by_name():
    global _mapping_files
    if _mapping_files is None:
        _mapping_files = dict()
        with os.scandir(os.path.join(os.path.dirname(__file__), '../mappings')) as directory:
            for entry in directory:
                if not entry.name.startswith('.') and entry.name.endswith('.json') and entry.is_file():
                    _mapping_files[entry.name.rsplit('.', 1)[0]] = entry.path
    return _mapping_files
