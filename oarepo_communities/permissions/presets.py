from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from invenio_records_permissions.policies.base import BasePermissionPolicy

from .record import CommunityRolePermittedInCF


class CommunityPermissionPolicy(RecordPermissionPolicy):
    # todo imo this might be any or authenticated, unless the ability to search at all is being restricted by community membership
    # that would also allow communities to limit searching of their own records, though is that really meaningful?
    # we also can't do the only system process trick here bc it query filter needs the right identity to work correctly
    can_search = [
        SystemProcess(),
        AuthenticatedUser(),
    ]
    # the actual search query filter works through this
    can_read = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_read"),
    ]
    # for this to work we have to disable create entrypoint and use only create in community, where the actual permission is set
    # alternatively, put the permission here, and then we have to rewrite the service method because invenio has no way to push the users community
    can_create = [
        SystemProcess(),
    ]
    can_update = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_update"),
    ]
    can_delete = [
        SystemProcess(),
    ]
    can_manage = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_manage"),
    ]

    can_create_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_create_files"),
    ]
    can_set_content_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_set_content_files"),
    ]
    can_get_content_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_get_content_files"),
    ]
    can_commit_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_commit_files"),
    ]
    can_read_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_read_files"),
    ]
    can_update_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_update_files"),
    ]
    can_delete_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_delete_files"),
    ]

    can_edit = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_edit"),
    ]
    can_new_version = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_new_version"),
    ]
    # todo?
    can_search_drafts = [
        SystemProcess(),
        AuthenticatedUser(),
    ]
    can_read_draft = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_read_draft"),
    ]
    can_update_draft = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_update_draft"),
    ]
    can_delete_draft = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_delete_draft"),
    ]
    can_publish = [
        SystemProcess(),
    ]
    can_draft_create_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_draft_create_files"),
    ]
    can_draft_set_content_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(
            community_permission_name="can_draft_set_content_files"
        ),
    ]
    can_draft_get_content_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(
            community_permission_name="can_draft_get_content_files"
        ),
    ]
    can_draft_commit_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_draft_commit_files"),
    ]
    can_draft_read_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_draft_read_files"),
    ]
    can_draft_update_files = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_draft_update_files"),
    ]


class CommunityRecordsEveryonePermissionPolicy(BasePermissionPolicy):
    can_create_in_community = [
        SystemProcess(),
        AnyUser(),
    ]


class CommunityRecordsCommunityPermissionPolicy(BasePermissionPolicy):
    can_create_in_community = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_create_in_community"),
    ]


class CommunityRequestsPermissionPolicy(BasePermissionPolicy):
    can_delete_request = (
        [
            SystemProcess(),
            CommunityRolePermittedInCF(community_permission_name="can_delete_request"),
        ],
    )

    can_publish_request = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_publish_request"),
    ]
    can_add_secondary_community = [
        SystemProcess(),
        CommunityRolePermittedInCF(
            community_permission_name="can_submit_secondary_community"
        ),
    ]
