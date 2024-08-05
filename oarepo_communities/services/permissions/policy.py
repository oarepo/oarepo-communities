from invenio_records_permissions import RecordPermissionPolicy
from oarepo_requests.services.permissions.workflow_policies import (
    DefaultWithRequestsWorkflowPermissionPolicy,
)
from oarepo_workflows import WorkflowPermission

from oarepo_communities.services.permissions.generators import CommunityMembers


# todo specify
class CommunityDefaultWorkflowPermissions(DefaultWithRequestsWorkflowPermissionPolicy):
    can_create = [
        CommunityMembers(),
    ]

    can_set_workflow = [CommunityMembers()]


class OARepoCommunityWorkflowPermissionPolicy(RecordPermissionPolicy):

    can_set_workflow = [WorkflowPermission("can_set_workflow")]
