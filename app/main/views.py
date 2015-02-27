from flask import jsonify, url_for, request
from . import main, search_service
from .search_result_formatters import SearchResults


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
def keyword_query_with_optional_filters():
    response = search_service.keyword_query_with_filters(request.args)
    search_results_obj = SearchResults(response)
    return jsonify(search_results_obj.get_results())
