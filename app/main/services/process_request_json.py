import types
from query_builder import FILTER_FIELDS
from conversions import strip_and_lowercase


def process(request_json, key):
    values = request_json[key]

    if isinstance(values, types.ListType):
        fixed = []
        for i in values:
            fixed.append(strip_and_lowercase(i))
        return fixed
    elif isinstance(values, basestring):
        return strip_and_lowercase(values)

    return values


def convert_request_json_into_index_json(request_json):
    exact_fields = [field for field in request_json if field in FILTER_FIELDS]

    for field in exact_fields:
        request_json["{}Exact".format(field)] = process(request_json, field)

    return request_json
