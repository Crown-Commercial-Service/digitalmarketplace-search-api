from flask import current_app, abort, request

from dmutils.authentication import UnauthorizedWWWAuthenticate


def requires_authentication(module="main"):
    if current_app.config['AUTH_REQUIRED']:
        incoming_token = get_token_from_headers(request.headers)

        if not incoming_token:
            raise UnauthorizedWWWAuthenticate(
                www_authenticate=f"Bearer realm={module}",
                description="Unauthorized; bearer token must be provided",
            )
        if not token_is_valid(incoming_token):
            abort(403, incoming_token)


def token_is_valid(incoming_token):
    return incoming_token in get_allowed_tokens_from_config(current_app.config)


def get_allowed_tokens_from_config(config):
    """Return a list of allowed auth tokens from application config"""
    return [token for token in config.get('DM_SEARCH_API_AUTH_TOKENS', '').split(':') if token]


def get_token_from_headers(headers):
    auth_header = headers.get('Authorization', '')
    if auth_header[:7] != 'Bearer ':
        return None
    return auth_header[7:]
