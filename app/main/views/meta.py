from flask import jsonify, url_for

from dmutils.timing import logged_duration_for_external_request

from app.main import main
from app import elasticsearch_client as es

import app.mapping


@main.route('/')
def root():
    """Entry point for the API, show the resources that are available."""
    with logged_duration_for_external_request('es'):
        es_indices = es.indices.get_mapping().items()

    def types_from_index(index: dict) -> list:
        mappings = index["mappings"]
        if "_meta" in mappings:
            # this is a hack, we should really stop including document types
            # in our urls but for now we squirrel the information away in _meta
            return [mappings["_meta"]["doc_type"]]
        else:
            return mappings.keys()

    types_by_index_name: dict[str, list] = {
        index_name: types_from_index(index_info)
        for index_name, index_info in es_indices
        if not index_name.startswith('.')
    }
    links = list()
    for index_name, types in types_by_index_name.items():
        for type_name in types:
            links.append({
                "rel": "query.gdm.index",
                "href": url_for('.search',
                                index_name=index_name,
                                doc_type=type_name,
                                _external=True)})

    with logged_duration_for_external_request('es'):
        es_alias_json = es.cat.aliases(format='json')

    aliases = {
        info['alias']: info['index']
        for info in es_alias_json
        if not info['index'].startswith('.')
    }
    for alias_name, index_name in aliases.items():
        for type_name in types_by_index_name[index_name]:
            links.append({
                "rel": "query.gdm.alias",
                "href": url_for('.search',
                                index_name=alias_name,
                                doc_type=type_name,
                                _external=True)})
    return jsonify(
        {
            'links': links,
            'field-mappings': [name for name in app.mapping.get_mapping_file_paths_by_name().keys()],
        }
    ), 200
