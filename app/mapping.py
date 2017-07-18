from flask import json


SERVICES_MAPPING_FILE_SPEC = "mappings/services.json"

_services = None


class Mapping(object):
    def __init__(self, mapping_definition, mapping_type):
        self.definition = mapping_definition
        self._filter_fields = tuple(sorted(
            field.replace('filter_', '')
            for field in self.definition['mappings'][mapping_type]['properties'].keys()
            if field.startswith('filter_'))
        )
        self.filter_fields_set = frozenset(self._filter_fields)
        self.text_fields = tuple(sorted(
            field
            for field in self.definition['mappings'][mapping_type]['properties'].keys()
            if not field.startswith('filter_')
        ))
        self.text_fields_set = frozenset(self.text_fields)
        self.aggregatable_fields = tuple(sorted(
            k
            for k, v in self.definition['mappings'][mapping_type]['properties'].items()
            if v.get('fields', {}).get('raw', False)
        ))
        self.transform_fields = tuple(self.definition['mappings'][mapping_type]['_meta']['transformations'])


def get_services_mapping():
    # mockable singleton - see conftest.py
    global _services
    if _services is None:
        with open(SERVICES_MAPPING_FILE_SPEC) as services_file:
            _services = Mapping(json.load(services_file), 'services')
    return _services
