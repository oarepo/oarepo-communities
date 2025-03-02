from invenio_records_permissions.generators import (
    SystemProcess,
)
from oarepo_requests.services.permissions.workflow_policies import (
    RequestBasedWorkflowPermissions,
)
from oarepo_workflows import WorkflowRecordPermissionPolicy

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

    can_add_community = [SystemProcess()]
    """Can add community to record"""

    can_remove_community = [SystemProcess()]
    """Can remove community from record"""

    can_remove_record = [SystemProcess()]
    """Can remove record from community"""


class CommunityWorkflowPermissionPolicy(WorkflowRecordPermissionPolicy):
    can_create = [CommunityWorkflowPermission("create")]
    can_view_deposit_page = [InAnyCommunity(CommunityWorkflowPermission("create"))]
