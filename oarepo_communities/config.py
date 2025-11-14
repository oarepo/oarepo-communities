#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration for oarepo-communities."""

from __future__ import annotations

from invenio_communities.config import COMMUNITIES_ROUTES as INVENIO_COMMUNITIES_ROUTES
from invenio_i18n import lazy_gettext as _

from .services.custom_fields.workflow import WorkflowCF, lazy_workflow_options

# from .notifications.generators import CommunityRoleEmailRecipient # noqa

OAREPO_REQUESTS_DEFAULT_RECEIVER = "oarepo_requests.receiver.default_workflow_receiver_function"
REQUESTS_ALLOWED_RECEIVERS = ["community_role"]


DEFAULT_COMMUNITIES_CUSTOM_FIELDS = [
    WorkflowCF(name="workflow"),
    WorkflowCF(name="allowed_workflows", multiple=True),
]

DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI = [
    {
        "section": _("Workflows"),
        "fields": [
            {
                "field": "workflow",
                "ui_widget": "Dropdown",
                "props": {
                    "label": _("Default workflow"),
                    "description": _(
                        "Default workflow for the community if workflow is not specified when depositing a record."
                    ),
                    "options": lazy_workflow_options,
                },
            },
            {
                "field": "allowed_workflows",
                # TODO: need to find a better widget for this
                "ui_widget": "Dropdown",
                "props": {
                    "label": _("Allowed workflows"),
                    "multiple": True,
                    "description": _("Workflows allowed for the community."),
                    "options": lazy_workflow_options,
                },
            },
        ],
    }
]

COMMUNITIES_ROUTES = {**INVENIO_COMMUNITIES_ROUTES, "my_communities": "/me/communities"}

DISPLAY_USER_COMMUNITIES = True

DISPLAY_NEW_COMMUNITIES = True

# NOTIFICATION_RECIPIENTS_RESOLVERS = {"community_role": {"email": CommunityRoleEmailRecipient}} # noqa


COMMUNITIES_RECORDS_SEARCH_ALL = False

# name of the default workflow for communities. It is used when a community does not have
# an explicit workflow set
OAREPO_COMMUNITIES_DEFAULT_WORKFLOW = "default"
