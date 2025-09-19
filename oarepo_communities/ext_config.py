#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from oarepo_communities.services.permissions.policy import (
    CommunityWorkflowPermissionPolicy,
)
from oarepo_communities.worklows.permissive_workflow import PermissiveWorkflow

OAREPO_PERMISSIONS_PRESETS = {
    "community-workflow": CommunityWorkflowPermissionPolicy,
}

COMMUNITY_WORKFLOWS = {
    "default": PermissiveWorkflow(),
}

DEFAULT_COMMUNITIES_ROLES = [
    dict(
        name="member",
        title="Member",
        description="Community member.",
    ),
    dict(
        name="owner",
        title="Community owner",
        description="Can manage community.",
        is_owner=True,
        can_manage=True,
        can_manage_roles=["owner", "member"],
    ),
]


# name of the default workflow for communities. It is used when a community does not have
# an explicit workflow set
OAREPO_COMMUNITIES_DEFAULT_WORKFLOW = "default"
