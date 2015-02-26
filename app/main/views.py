from . import main
from flask import jsonify, url_for, Response


@main.route('/')
def index():
    """Entry point for the API, show the resources that are available."""
    return jsonify(links=[
        {
            "rel": "query.gdm.index",
            "href": url_for('.keyword_query', _external=True)
        }
    ]), 200


@main.route('/search', methods=['GET'])
def keyword_query():
    return Response("Not yet implemented... come back later!"), 202
