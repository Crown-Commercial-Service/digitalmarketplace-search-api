import hashlib
from itertools import chain

import six
from flask import request
from werkzeug.exceptions import abort


def _ensure_value_list(json_string_or_list):
    if isinstance(json_string_or_list, list):
        return json_string_or_list
    else:
        return [json_string_or_list]


def _update_conditionally(arguments, document):
    """
    A transformation processor that updates field values in "target field" when
    certain values are present in "field". The example use case is when
    we are converting awarded, unsuccessful or cancelled brief status to closed.
    :param arguments: dict -- the parameters to the processor as specified in configuration
    :param document: dict -- the submitted document that we are transforming
    """
    _append_conditionally(arguments, document, update=True)


def _append_conditionally(arguments, document, update=False):
    """
    A transformation processor that generates new field values in "target field" when
    certain values are present in "field". The example use case is when
    we are adding parent categories, whenever any one of their subcategories
    is present.
    :param arguments: dict -- the parameters to the processor as specified in configuration
    :param document: dict -- the submitted document that we are transforming
    :param update: bool -- if true, then the target field is updated instead of appended to. See the function above.
    """
    source_field = arguments['field']
    target_field = arguments.get('target_field') or source_field

    if source_field in document:
        source_values = _ensure_value_list(document[source_field])
        source_values_set = set(source_values)
        target_values = _ensure_value_list(document.get(target_field, []))

        if any(value in source_values_set for value in arguments['any_of']):
            if update:
                document[target_field] = arguments['update_value']
            else:
                target_values.extend(arguments['append_value'])
                # "append_value" key singular despite being a list, consistent with Elasticsearch practice
                document[target_field] = target_values


def _hash_to(arguments, document):
    """
    A transformation processor that performs a sha256 on the (utf8) string representation of the "field" and stores
    the (lowercase hex string) result on the document under a key specified by "target_field". If "target_field" is not
    specified, the source field will be overwritten with the result.
    :param arguments: dict -- the parameters to the processor as specified in configuration
    :param document: dict -- the submitted document that we are transforming
    """
    source_field = arguments['field']
    target_field = arguments.get('target_field') or source_field

    if source_field in document:
        document[target_field] = hashlib.sha256((six.text_type(document[source_field])).encode('utf-8')).hexdigest()


TRANSFORMATION_PROCESSORS = {
    'append_conditionally': _append_conditionally,
    'update_conditionally': _update_conditionally,
    'hash_to': _hash_to,
}


def convert_request_json_into_index_json(mapping, request_json):
    for transformation in mapping.transform_fields:
        # Each transformation is a dictionary, with a type mapping to the arguments pertaining to
        # that type. We anticipate only one type per transformation (consistent with how 'ingest
        # processors' are specified for Elasticsearch - see
        # <https://www.elastic.co/guide/en/elasticsearch/reference/current/ingest-processors.html>).

        for transformation_type, transformation_arguments in transformation.items():
            TRANSFORMATION_PROCESSORS[transformation_type](transformation_arguments, request_json)

    # build a dict: for each key/value in the request_json, look up mapping.prefixes_by_field to see how many
    # differently-prefixed variants that field has in the mapping and copy value verbatim to all those keys. it could
    # of course have no representation in the mapping, in which case it would be ignored.
    return dict(chain.from_iterable(
        (
            ("_".join((prefix, key)), value)
            for prefix in mapping.prefixes_by_field.get(key, ())
        )
        for key, value in request_json.items()
    ))


def check_json_from_request(request):
    if request.content_type not in ['application/json',
                                    'application/json; charset=UTF-8']:
        abort(400, "Unexpected Content-Type, expecting 'application/json'")

    data = request.get_json()

    if data is None:
        abort(400, "Invalid JSON; must be a valid JSON object")
    return data


def json_has_required_keys(data, keys):
    for key in keys:
        if key not in data.keys():
            abort(400, "Invalid JSON must have '%s' key(s)" % keys)


def get_json_from_request(root_field):
    payload = check_json_from_request(request)
    json_has_required_keys(payload, [root_field])
    update_json = payload[root_field]
    return update_json
