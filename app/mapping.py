from flask import json


with open("mappings/services.json") as services:
    SERVICES_MAPPING = json.load(services)

FILTER_FIELDS = sorted(
    field.replace('filter_', '')
    for field in SERVICES_MAPPING['mappings']['services']['properties'].keys()
    if field.startswith('filter_')
)

TEXT_FIELDS = sorted(
    field
    for field in SERVICES_MAPPING['mappings']['services']['properties'].keys()
    if not field.startswith('filter_')
)

AGGREGATABLE_FIELDS = sorted(
    k
    for k, v in SERVICES_MAPPING['mappings']['services']['properties'].items()
    if v.get('fields', {}).get('raw', False)
)

TRANSFORM_FIELDS = SERVICES_MAPPING['mappings']['services']['_meta']['transformations']
