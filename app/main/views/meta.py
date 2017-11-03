from flask import jsonify, url_for

from app.main import main
import app.mapping


@main.route('/')
def root():
    """Entry point for the API, show the resources that are available."""
    return jsonify(
        {
            'links': [
                {
                    "rel": "query.gdm.index",
                    "hrefs": url_for('.search',
                                     index_name="index-name",
                                     doc_type="doc-type",
                                     _external=True)
                }
            ],
            'field-mappings': [name for name in app.mapping.get_mapping_file_paths_by_name().keys()],
        }
    ), 200
