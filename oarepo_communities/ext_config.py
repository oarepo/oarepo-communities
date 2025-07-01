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
