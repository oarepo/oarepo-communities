from invenio_records_permissions.generators import AnyUser
from oarepo_requests.permissions.generators import RequestActive
from oarepo_runtime.services.generators import RecordOwners
from oarepo_workflows.permissions.generators import IfInState
from oarepo_workflows.permissions.policy import DefaultWorkflowPermissionPolicy

from oarepo_communities.permissions.generators import CommunityMembers, CommunityRole


class CommunityDefaultWorkflowPermissions(DefaultWorkflowPermissionPolicy):
    can_create_in_community = [
        CommunityMembers(),
    ]
    can_create = [
        CommunityMembers(),
    ]
    can_read = [
        RecordOwners(),
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
