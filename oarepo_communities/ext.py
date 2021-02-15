# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import request
from invenio_base.signals import app_loaded
from . import config


@app_loaded.connect
def add_urlkwargs(sender, app, **kwargs):

    def _community_urlkwargs(endpoint, values):
        if 'community_id' not in values:
            values['community_id'] = request.view_args['community_id']

    app.url_default_functions.setdefault('invenio_records_rest', []).append(_community_urlkwargs)


class OARepoCommunities(object):
    """OARepo-Communities extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['oarepo-communities'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed

        for k in dir(config):
            if k.startswith('OAREPO_COMMUNITIES_'):
                app.config.setdefault(k, getattr(config, k))
