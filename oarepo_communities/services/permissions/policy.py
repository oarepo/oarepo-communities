from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)
from oarepo_requests.services.permissions.workflow_policies import (
    RequestBasedWorkflowPermissions,
)
from oarepo_workflows import WorkflowRecordPermissionPolicy
from oarepo_workflows.requests.generators.conditionals import IfRequestType
from oarepo_workflows.requests.permissions import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)

from oarepo_communities.services.permissions.generators import (
    CommunityWorkflowPermission,
    DefaultCommunityMembers,
    InAnyCommunity,
)


class CommunityDefaultWorkflowPermissions(RequestBasedWorkflowPermissions):
    """
    Base class for community workflow permissions, subclass from it and put the result to Workflow constructor.
    Example:
        class MyWorkflowPermissions(CommunityDefaultWorkflowPermissions):
            can_read = [AnyUser()]
    in invenio.cfg
    WORKFLOWS = {
        'default': Workflow(
            permission_policy_cls = MyWorkflowPermissions, ...
        )
    }
    """

    can_create = [
        DefaultCommunityMembers(),
    ]


class CommunityWorkflowPermissionPolicy(WorkflowRecordPermissionPolicy):
    can_create = [CommunityWorkflowPermission("create")]
    can_view_deposit_page = [InAnyCommunity(CommunityWorkflowPermission("create"))]


class CommunityRequestsWorkflowPermissionPolicy(
    CreatorsFromWorkflowRequestsPermissionPolicy
):
    can_create = CreatorsFromWorkflowRequestsPermissionPolicy.can_create + [
        IfRequestType(
            ["community-invitation"], InvenioRequestsPermissionPolicy.can_create
        )
    ]
