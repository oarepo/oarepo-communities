from oarepo_requests.services.permissions.workflow_policies import (
    DefaultWithRequestsWorkflowPermissionPolicy,
)
from oarepo_communities.services.permissions.generators import DefaultCommunityMembers


# todo specify
class CommunityDefaultWorkflowPermissions(DefaultWithRequestsWorkflowPermissionPolicy):
    can_create = [
        DefaultCommunityMembers(),
    ]
    # set community workflow permissions now set via update of community record via custom field