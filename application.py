#!/usr/bin/env python

import os

from dmutils import init_manager

from app import create_app

application = create_app(os.getenv('DM_ENVIRONMENT') or 'development')
manager = init_manager(application, 5000, ['./json_schemas'])


@manager.command
def update_index(index_name):
    from app.main.services.search_service import create_index
    with application.app_context():
        message, status = create_index(index_name)
    assert status == 200, message
    application.logger.info("Created index %s", index_name)


if __name__ == '__main__':
    manager.run()
