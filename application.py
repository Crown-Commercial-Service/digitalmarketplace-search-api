#!/usr/bin/env python

import os

from dmutils import init_manager

from app import create_app

application = create_app(os.getenv('DM_ENVIRONMENT') or 'development')
manager = init_manager(application, 5009, ['./mappings'])


if __name__ == '__main__':
    manager.run()
