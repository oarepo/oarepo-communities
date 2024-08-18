from oarepo_communities.services.permissions.policy import (
    CommunityWorkflowPermissionPolicy,
)
from oarepo_communities.worklows.permissive_workflow import PermissiveWorkflow

OAREPO_PERMISSIONS_PRESETS = {
    "community-workflow": CommunityWorkflowPermissionPolicy,
}

COMMUNITY_WORKFLOWS = {
    'default': PermissiveWorkflow(),
}