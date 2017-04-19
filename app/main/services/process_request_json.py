import six

from ...mapping import FILTER_FIELDS, TEXT_FIELDS, TRANSFORM_FIELDS
from .conversions import strip_and_lowercase

FILTER_FIELDS_SET = set(FILTER_FIELDS)
TEXT_FIELDS_SET = set(TEXT_FIELDS)


def process_values_for_matching(values):
    if isinstance(values, list):
        return [strip_and_lowercase(value) for value in values]
    elif isinstance(values, six.string_types):
        return strip_and_lowercase(values)

    return values


def _ensure_value_list(json_string_or_list):
    if isinstance(json_string_or_list, list):
        return json_string_or_list
    else:
        return [json_string_or_list]


def convert_request_json_into_index_json(request_json):
    index_json = {}

    for transformation in TRANSFORM_FIELDS:
        # Each transformation can generate new field values in "target field" when
        # certain values are present in "field". The example use case is when
        # we are adding parent categories, whenever any one of their subcategories
        # is present.
        source_field = transformation['field']
        target_field = transformation.get('target_field') or source_field

        if source_field in request_json:
            source_values = _ensure_value_list(request_json[source_field])
            source_values_set = set(source_values)
            target_values = _ensure_value_list(request_json[target_field])

            if any(value in source_values_set for value in transformation['any_of']):
                target_values.extend(transformation['append_value'])
                # "append_value" key singular despite being a list, consistent with Elasticsearch practice
                request_json[target_field] = target_values

    for field in request_json:
        if field in FILTER_FIELDS_SET:
            index_json["filter_" + field] = process_values_for_matching(
                request_json[field]
            )
        if field in TEXT_FIELDS_SET:
            index_json[field] = request_json[field]

    return index_json
