# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_base.utils import load_or_import_from_config
from werkzeug.utils import cached_property

from flask import request
from invenio_base.signals import app_loaded
from . import config


@app_loaded.connect
def add_urlkwargs(sender, app, **kwargs):

    def _community_urlkwargs(endpoint, values):
        if 'community_id' not in values:
            values['community_id'] = request.view_args['community_id']

    app.url_default_functions.setdefault('invenio_records_rest', []).append(_community_urlkwargs)


class _OARepoCommunitiesState(object):
    """Invenio Files REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app

    @cached_property
    def roles(self):
        """Roles created in each community."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ROLES', app=self.app)

    @cached_property
    def actions_policy(self):
        """Roles created in each community."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ACTIONS_POLICY', app=self.app)

    @cached_property
    def role_name_factory(self):
        """Load default factory that returns role name for community-based roles."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ROLE_NAME', app=self.app)

    @cached_property
    def role_parser(self):
        """Load default factory that parses community id and role from community role names."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ROLE_PARSER', app=self.app)

    @cached_property
    def permission_factory(self):
        """Load default permission factory for Community record collections."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_PERMISSION_FACTORY', app=self.app
        )


class OARepoCommunities(object):
    """OARepo-Communities extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['oarepo-communities'] = _OARepoCommunitiesState(app)

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed

        for k in dir(config):
            if k.startswith('OAREPO_COMMUNITIES_'):
                app.config.setdefault(k, getattr(config, k))
