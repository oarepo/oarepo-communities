from invenio_records_permissions import RecordPermissionPolicy
from oarepo_requests.services.permissions.workflow_policies import (
    DefaultWithRequestsWorkflowPermissionPolicy,
)
from oarepo_workflows import WorkflowPermission

from oarepo_communities.services.permissions.generators import DefaultCommunityMembers


# todo specify
class CommunityDefaultWorkflowPermissions(DefaultWithRequestsWorkflowPermissionPolicy):
    can_create = [
        DefaultCommunityMembers(),
    ]

    can_set_workflow = [DefaultCommunityMembers()]


class OARepoCommunityWorkflowPermissionPolicy(RecordPermissionPolicy):

    can_set_workflow = [WorkflowPermission("can_set_workflow")]
