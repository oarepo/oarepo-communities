# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import request
from flask_login import current_user
from flask_principal import identity_loaded
from invenio_base.signals import app_loaded
from invenio_base.utils import load_or_import_from_config
from oarepo_ui.proxy import current_oarepo_ui
from werkzeug.utils import cached_property

from . import config
from .permissions import community_record_owner


@app_loaded.connect
def add_urlkwargs(sender, app, **kwargs):
    # ziskat vsechna listing url pro komunity
    eps = app.config['OAREPO_COMMUNITIES_ENDPOINTS']
    for ep in eps:
        app.extensions['oarepo-communities'].list_endpoints.add(f'invenio_records_rest.{ep}_list')

    def _community_urlkwargs(endpoint, values):
        # TODO: config option for endpoints that need community_id kwarg
        if endpoint in app.extensions['oarepo-communities'].list_endpoints:
            if 'community_id' not in values:
                values['community_id'] = request.view_args['community_id']

    app.url_default_functions.setdefault('invenio_records_rest', []).append(_community_urlkwargs)


class _OARepoCommunitiesState(object):
    """Invenio Files REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        self.list_endpoints = set()

    @cached_property
    def roles(self):
        """Roles created in each community."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ROLES', app=self.app)

    @cached_property
    def enabled_endpoints(self):
        """List of community-enabled REST endpoints."""
        enabled_endpoints = load_or_import_from_config(
            'OAREPO_COMMUNITIES_ENDPOINTS', app=self.app)
        return [e for e in current_oarepo_ui.endpoints if e['name'] in enabled_endpoints]

    @cached_property
    def allowed_actions(self):
        """Community actions available to community roles."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_ALLOWED_ACTIONS', app=self.app)

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
        state = _OARepoCommunitiesState(app)

        app.extensions['oarepo-communities'] = state

        identity_loaded.connect_via(app)(on_identity_loaded)

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed

        for k in dir(config):
            if k.startswith('OAREPO_COMMUNITIES_'):
                app.config.setdefault(k, getattr(config, k))


def on_identity_loaded(sender, identity):
    if current_user.is_authenticated:
        # Any authenticated user could be a community record owner.
        identity.provides.add(community_record_owner)
