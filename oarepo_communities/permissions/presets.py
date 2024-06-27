from invenio_communities.generators import CommunityMembers
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess, AnyUser
from invenio_records_permissions.policies.base import BasePermissionPolicy
from oarepo_requests.permissions.generators import RequestActive
from oarepo_runtime.services.generators import RecordOwners
from oarepo_workflows.permissions.generators import IfInState

from oarepo_communities.permissions.generators import CommunityRole

"""
class CommunityRequestsPermissionPolicy(BasePermissionPolicy):
    can_delete_request = (
        [
            SystemProcess(),
            WorkflowRequestPermission(access_key="creators"),
        ],
    )

    can_publish_request = [
        SystemProcess(),
        WorkflowRequestPermission(access_key="creators"),
    ]
    can_add_secondary_community = [
        SystemProcess(),
        WorkflowRequestPermission(access_key="creators"),
    ]
"""

from invenio_records_permissions import RecordPermissionPolicy
from oarepo_workflows.permissions.policy import WorkflowPermissionPolicy
class CommunityDefaultWorkflowPermissions(WorkflowPermissionPolicy):
    can_create_in_community = [
        CommunityMembers(),
    ]
    can_create = [
        CommunityMembers(),
    ]
    can_read = [
        RecordOwners(),
        CommunityRole("owner"),
        IfInState("published",
                      [AnyUser()],
                  ),
    ]

    can_update = [
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("published", [CommunityRole("owner")]),
    ]

    can_delete = [
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("published", [RequestActive()]),
    ]

    can_publish = [RequestActive()]