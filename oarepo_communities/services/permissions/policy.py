from oarepo_requests.services.permissions.workflow_policies import (
    DefaultWithRequestsWorkflowPermissionPolicy,
)
from oarepo_workflows.services.permissions.policy import WorkflowPermissionPolicy

from oarepo_communities.services.permissions.generators import (
    CommunityWorkflowPermission,
    DefaultCommunityMembers,
    InAnyCommunity,
)


# todo specify
class CommunityDefaultWorkflowPermissions(DefaultWithRequestsWorkflowPermissionPolicy):
    can_create = [
        DefaultCommunityMembers(),
    ]


class CommunityWorkflowPermissionPolicy(WorkflowPermissionPolicy):
    can_create = [CommunityWorkflowPermission("create")]
    can_view_deposit_page = [InAnyCommunity(CommunityWorkflowPermission("create"))]
