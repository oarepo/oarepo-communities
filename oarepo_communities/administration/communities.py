# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio administration OAI-PMH view module."""
from functools import partial

from flask import current_app
from invenio_administration.views.base import (
    AdminResourceDetailView,
    AdminResourceListView, AdminResourceCreateView, AdminResourceEditView,
)
from invenio_search_ui.searchconfig import search_app_config

from invenio_communities.communities.schema import CommunityFeaturedSchema

from invenio_i18n import lazy_gettext as _

import marshmallow as ma

class CommunityListView(AdminResourceListView):
    """Search admin view."""

    api_endpoint = "/communities"
    name = "oarepo-communities"
    resource_config = "communities_resource"
    search_request_headers = {"Accept": "application/vnd.inveniordm.v1+json"}
    title = _("Communities")
    menu_label = _("Communities")
    category = "Communities"
    pid_path = "id"
    icon = "users"
    template = "invenio_communities/administration/community_search.html"

    display_search = True
    display_delete = False
    display_create = True
    display_edit = True

    create_view_name = "oarepo_community_create"

    item_field_list = {
        "slug": {"text": "Slug", "order": 1, "width": 1},
        "metadata.title": {"text": "Title", "order": 2, "width": 4},
        "ui.type.title_l10n": {"text": "Type", "order": 3, "width": 2},
        "featured": {"text": "Featured", "order": 4, "width": 1},
        "created": {"text": "Created", "order": 5, "width": 2},
    }

    actions = {
        "featured": {
            "text": _("Feature"),
            "payload_schema": CommunityFeaturedSchema,
            "order": 1,
        },
        # custom components in the UI
        "delete": {
            "text": _("Delete"),
            "payload_schema": None,
            "order": 2,
        },
        # custom components in the UI
        "restore": {
            "text": _("Restore"),
            "payload_schema": None,
            "order": 2,
        },
    }
    search_config_name = "COMMUNITIES_SEARCH"
    search_facets_config_name = "COMMUNITIES_FACETS"
    search_sort_config_name = "COMMUNITIES_SORT_OPTIONS"

    def init_search_config(self):
        """Build search view config."""
        return partial(
            search_app_config,
            config_name=self.get_search_app_name(),
            available_facets=current_app.config.get(self.search_facets_config_name),
            sort_options=current_app.config[self.search_sort_config_name],
            endpoint=self.get_api_endpoint(),
            headers=self.get_search_request_headers(),
            initial_filters=[["status", "P"]],
            hidden_params=[
                ["include_deleted", "1"],
            ],
            page=1,
            size=30,
        )

class AddCuratorSchema(ma.Schema):
    curator = ma.fields.String(required=True, metadata={"type_override": "Blah.jsx"})

class CommunityDetailView(AdminResourceDetailView):
    """Admin community detail view."""

    url = "/oarepo-communities/<pid_value>"
    api_endpoint = "/communities"
    name = "oarepo-community-details"
    resource_config = "communities_resource"
    title = _("Community")

    # template = "invenio_communities/administration/community_details.html"
    display_delete = False
    display_edit = False

    list_view_name = "oarepo-communities"
    pid_path = "id"
    request_headers = {"Accept": "application/vnd.inveniordm.v1+json"}

    actions = {
        "add_curator": {
            "text": _("Add Curator"),
            "payload_schema": AddCuratorSchema,
            "order": 2,
        },
        "remove_curator": {
            "text": _("Remove Curator"),
            "payload_schema": None,
            "order": 3,
        },
    }

    item_field_list = {
        "slug": {
            "text": "Slug",
            "order": 1,
        },
        "metadata.title": {"text": "Title", "order": 2},
        "created": {"text": "Created", "order": 5},
    }

    def _schema_to_json(self, schema):
        ret = super()._schema_to_json(schema)
        for k, v in ret.items():
            type_override = v.get('metadata', {}).get("type_override")
            if type_override:
                v['type'] = type_override
        return ret

COMMUNITY_EDIT_FIELDS = {
    "metadata.title": {
            "order": 2,
            "text": _("Community Name"),
        },
        "metadata.description": {
            "order": 3,
            "text": _("Community Description"),
            "rows": 10,
        },
        "access.visibility": {
            "order": 4,
            "text": _("Visibility"),
            "options": [
                {"title_l10n": "Public", "id": "public"},
                {"title_l10n": "Restricted", "id": "restricted"},
            ],
        },
        "access.members_visibility": {
            "order": 5,
            "text": _("Members Visibility"),
            "options": [
                {"title_l10n": "Public", "id": "public"},
                {"title_l10n": "Restricted", "id": "restricted"},
            ],
        }
}


class CommunityCreateView(AdminResourceCreateView):
    """Configuration for Banner create view."""

    name = "oarepo_community_create"
    url = "/oarepo-communities/create"
    resource_config = "communities_resource"
    pid_path = "id"
    api_endpoint = "/communities"
    title = _("Create Community")

    list_view_name = "oarepo-communities"

    form_fields = {
        "slug": {
            "order": 1,
            "text": _("Community Slug"),
        },
        **COMMUNITY_EDIT_FIELDS,
        # "access.member_policy": {
        #     "order": 3,
        #     "text": _("Member Policy"),
        #     "options": [
        #         {"title_l10n": "Open", "id": "open"},
        #         {"title_l10n": "Closed", "id": "closed"},
        #     ],
        # },
        # "access.record_policy": {
        #     "order": 4,
        #     "text": _("Record Policy"),
        #     "options": [
        #         {"title_l10n": "Open", "id": "open"},
        #         {"title_l10n": "Closed", "id": "closed"},
        #     ],
        # },
        # "access.review_policy": {
        #     "order": 5,
        #     "text": _("Review Policy"),
        #     "options": [
        #         {"title_l10n": "Open", "id": "open"},
        #         {"title_l10n": "Closed", "id": "closed"},
        #     ],
        # },
    }

    def _schema_to_json(self, schema):
        ret = super()._schema_to_json(schema)
        # TODO: probably bug in invenio schema_to_json, workaround
        if 'properties' in ret['metadata']:
            ret['metadata'].update(ret['metadata']['properties'])
        if 'properties' in ret['access']:
            ret['access'].update(ret['access']['properties'])
        ret.pop('custom_fields', None)
        ret.pop('theme', None)
        ret.pop('children', None)
        return ret


class CommunityEditView(AdminResourceEditView):
    """Configuration for Banner edit view."""

    name = "oarepo_community_edit"
    url = "/oarepo-communities/<pid_value>/edit"
    resource_config = "communities_resource"
    pid_path = "id"
    api_endpoint = "/communities"
    title = _("Edit Community")

    list_view_name = "oarepo-communities"

    form_fields = COMMUNITY_EDIT_FIELDS

    def _schema_to_json(self, schema):
        ret = super()._schema_to_json(schema)
        # TODO: probably bug in invenio schema_to_json, workaround
        if 'properties' in ret['metadata']:
            ret['metadata'].update(ret['metadata']['properties'])
        if 'properties' in ret['access']:
            ret['access'].update(ret['access']['properties'])
        ret.pop('custom_fields', None)
        ret.pop('theme', None)
        ret.pop('children', None)
        return ret
