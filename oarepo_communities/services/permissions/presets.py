from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, AuthenticatedUser
from oarepo_requests.services.permissions.generators import RequestActive
from oarepo_runtime.services.permissions import RecordOwners
from oarepo_workflows import (
    DefaultWorkflowPermissionPolicy,
    IfInState,
    WorkflowPermission,
)

from oarepo_communities.services.permissions.generators import (
    CommunityMembers,
    CommunityRole,
)


class CommunityDefaultWorkflowPermissions(DefaultWorkflowPermissionPolicy):
    can_create_in_community = [
        CommunityMembers(),
    ]
    can_create = [
        CommunityMembers(),
    ]
    can_read = [
        RecordOwners(),
        AuthenticatedUser(),  # need for request receivers - temporary
        CommunityRole("owner"),
        IfInState(
            "published",
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
        IfInState("deleting", [RequestActive()]),
    ]

    can_publish = [RequestActive()]

    can_set_workflow = [CommunityMembers()]


class OARepoCommunityWorkflowPermissionPolicy(RecordPermissionPolicy):

    can_set_workflow = [WorkflowPermission("can_set_workflow")]
