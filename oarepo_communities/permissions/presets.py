from invenio_communities.generators import CommunityMembers
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from invenio_records_permissions.policies.base import BasePermissionPolicy
from oarepo_requests.permissions.generators import RequestActive
from oarepo_runtime.services.generators import RecordOwners

from .generators import WorkflowPermission, WorkflowRequestPermission


class CommunityPermissionPolicy(RecordPermissionPolicy):
    can_search = [
        SystemProcess(),
        AuthenticatedUser(),
    ]
    # the actual search query filter works through this
    can_read = [
        SystemProcess(),
        WorkflowPermission(access_key="readers"),
    ]
    can_create = [SystemProcess(), CommunityMembers()]
    can_update = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_delete = [SystemProcess(), RequestActive()]
    can_manage = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]

    can_create_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
        # WorkflowPermission(state='draft', role'=editor')
    ]
    can_set_content_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_get_content_files = [
        SystemProcess(),
        WorkflowPermission(access_key="readers"),
    ]
    can_commit_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_read_files = [
        SystemProcess(),
        WorkflowPermission(access_key="readers"),
    ]
    can_update_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_delete_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]

    can_edit = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_new_version = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_search_drafts = [
        SystemProcess(),
        AuthenticatedUser(),
    ]
    can_read_draft = [
        SystemProcess(),
        WorkflowPermission(access_key="readers"),
        RecordOwners(),
    ]
    can_update_draft = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
        RecordOwners(),
    ]
    can_delete_draft = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
        RecordOwners(),
    ]
    can_publish = [SystemProcess(), RequestActive()]
    can_draft_create_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_draft_set_content_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_draft_get_content_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_draft_commit_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]
    can_draft_read_files = [
        SystemProcess(),
        WorkflowPermission(access_key="readers"),
    ]
    can_draft_update_files = [
        SystemProcess(),
        WorkflowPermission(access_key="editors"),
    ]

    can_create_in_community = [
        SystemProcess(),
        CommunityMembers(),
    ]


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
