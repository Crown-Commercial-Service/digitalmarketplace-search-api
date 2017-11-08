from flask import jsonify, url_for

from app.main import main
from app import elasticsearch_client as es

import app.mapping


@main.route('/')
def root():
    """Entry point for the API, show the resources that are available."""
    types_by_index_name = {index_name: index_info['mappings'].keys()
                           for index_name, index_info in es.indices.get_mapping().items()
                           if not index_name.startswith('.')}
    links = list()
    for index_name, types in types_by_index_name.items():
        for type_name in types:
            links.append({
                "rel": "query.gdm.index",
                "href": url_for('.search',
                                index_name=index_name,
                                doc_type=type_name,
                                _external=True)})

    aliases = {info['alias']: info['index'] for info in es.cat.aliases(format='json')}
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
