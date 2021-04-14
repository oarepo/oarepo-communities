# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask_login import current_user
from flask_principal import identity_loaded
from invenio_base.signals import app_loaded
from invenio_base.utils import load_or_import_from_config
from oarepo_ui.proxy import current_oarepo_ui
from werkzeug.utils import cached_property

from . import config
from .permissions import community_record_owner
from .utils import community_id_from_request


@app_loaded.connect
def add_urlkwargs(sender, app, **kwargs):
    # ziskat vsechna listing url pro komunity
    eps = app.config['OAREPO_COMMUNITIES_ENDPOINTS']
    for ep in eps:
        app.extensions['oarepo-communities'].list_endpoints.add(f'invenio_records_rest.{ep}_list')

    def _community_urlkwargs(endpoint, values):
        if endpoint in app.extensions['oarepo-communities'].list_endpoints:
            if 'community_id' not in values:
                values['community_id'] = community_id_from_request()

    app.url_default_functions.setdefault('invenio_records_rest', []).append(_community_urlkwargs)


class _OARepoCommunitiesState(object):
    """Invenio Files REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        self.list_endpoints = set()
        self._primary_community_field = '_primary_community'
        self._primary_community_field_parsed = None
        self._owned_by_field = 'access.owned_by'
        self._owned_by_field_parsed = None
        self._communities_field = '_communities'
        self._communities_field_parsed = None

    @cached_property
    def default_action_matrix(self):
        """Default action2role permission matrix for newly created communities."""
        return load_or_import_from_config(
            'OAREPO_COMMUNITIES_DEFAULT_ACTIONS', app=self.app)

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

    @cached_property
    def primary_community_field(self):
        """Roles created in each community."""
        primary_community_field = self.app.config.get('OAREPO_COMMUNITIES_PRIMARY_COMMUNITY_FIELD')
        if primary_community_field:
            self._primary_community_field = primary_community_field
        return self._primary_community_field

    def get_primary_community_field(self, data):
        if not self._primary_community_field_parsed:
            self._primary_community_field_parsed = self.primary_community_field.split(".")
        for s in self._primary_community_field_parsed:
            if data:
                data = data.get(s)
        return data

    def set_primary_community_field(self, data, field):
        if not self._primary_community_field_parsed:
            self._primary_community_field_parsed = self.primary_community_field.split(".")
        for s in self._primary_community_field_parsed[:-1]:
            if s not in data:
                data[s] = {}
            data = data[s]
        data[self._primary_community_field_parsed[-1]] = field
        return data

    @cached_property
    def owned_by_field(self):
        """Roles created in each community."""
        owned_by_field = self.app.config.get('OAREPO_COMMUNITIES_OWNED_BY_FIELD')
        if owned_by_field:
            self._owned_by_field = owned_by_field
        return self._owned_by_field

    def get_owned_by_field(self, data):
        if not self._owned_by_field_parsed:
            self._owned_by_field_parsed = self.owned_by_field.split(".")
        for s in self._owned_by_field_parsed:
            if data:
                data = data.get(s)
        return data

    def set_owned_by_field(self, data, field):
        if not self._owned_by_field_parsed:
            self._owned_by_field_parsed = self.owned_by_field.split(".")
        for s in self._owned_by_field_parsed[:-1]:
            if s not in data:
                data[s] = {}
            data = data[s]
        data[self._owned_by_field_parsed[-1]] = field
        return data

    @cached_property
    def communities_field(self):
        """Roles created in each community."""
        communities_field = self.app.config.get('OAREPO_COMMUNITIES_COMMUNITIES_FIELD')
        if communities_field:
            self._communities_field = communities_field
        return self._communities_field

    def get_communities_field(self, data):
        if not self._communities_field_parsed:
            self._communities_field_parsed = self.communities_field.split(".")
        for s in self._communities_field_parsed:
            if data:
                data = data.get(s)
        return data

    def set_communities_field(self, data, field):
        if not self._communities_field_parsed:
            self._communities_field_parsed = self.communities_field.split(".")
        for s in self._communities_field_parsed[:-1]:
            if s not in data:
                data[s] = {}
            data = data[s]
        data[self._communities_field_parsed[-1]] = field
        return data

    @cached_property
    def facets(self):
        facets = {}
        for endpoint in self.enabled_endpoints:
            index_name = endpoint['config'].get('search_index')
            if index_name:
                index = current_oarepo_ui.facets.get(index_name)
                if index:
                    facets[index_name] = index['aggs']

        return facets


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
