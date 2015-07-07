import six

from ...mapping import FILTER_FIELDS, TEXT_FIELDS
from .conversions import strip_and_lowercase

FILTER_FIELDS_SET = set(FILTER_FIELDS)
TEXT_FIELDS_SET = set(TEXT_FIELDS)


def process_values_for_matching(values):
    if isinstance(values, list):
        return [strip_and_lowercase(value) for value in values]
    elif isinstance(values, six.string_types):
        return strip_and_lowercase(values)

    return values


def convert_request_json_into_index_json(request_json):
    index_json = {}

    for field in request_json:
        if field in FILTER_FIELDS_SET:
            index_json["filter_" + field] = process_values_for_matching(
                request_json[field]
            )
        if field in TEXT_FIELDS_SET:
            index_json[field] = request_json[field]

    return index_json
