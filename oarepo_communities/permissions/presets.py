from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from invenio_records_permissions.policies.base import BasePermissionPolicy

from .record import CommunityRolePermittedInCF


class CommunityPermissionPolicy(RecordPermissionPolicy):
    can_search = [
        SystemProcess(),
        AuthenticatedUser(), #the base service does not provide a way to check community in permissions
    ]
    can_read = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_read"),
    ]
    can_create = [SystemProcess(), AuthenticatedUser()]
    can_update = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_update"),
    ]
    can_delete = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_delete"),
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
    can_commit_files = [SystemProcess()], CommunityRolePermittedInCF(
        community_permission_name="can_commit_files"
    )
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
    can_search_drafts = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_search_drafts"),
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
        CommunityRolePermittedInCF(community_permission_name="can_publish"),
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


class RecordCommunitiesEveryonePermissionPolicy(BasePermissionPolicy):
    can_user_add_communities_to_records = [
        SystemProcess(),
        AnyUser(),
    ]
    can_community_allows_adding_records = [
        SystemProcess(),
        AnyUser(),
    ]
    can_remove_community_from_record = [
        SystemProcess(),
        AnyUser(),
    ]



class CommunityRecordsEveryonePermissionPolicy(BasePermissionPolicy):
    can_remove_records_from_community = [
        SystemProcess(),
        AnyUser(),
    ]


class RecordCommunitiesCommunityPermissionPolicy(BasePermissionPolicy):
    can_user_add_communities_to_records = [
        SystemProcess(),
        AuthenticatedUser(),
    ]
    can_community_allows_adding_records = [
        SystemProcess(),
        CommunityRolePermittedInCF(
            community_permission_name="can_community_allows_adding_records"
        ),
    ]
    can_remove_community_from_record = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_remove_community_from_record"),
    ]


class CommunityRecordsCommunityPermissionPolicy(BasePermissionPolicy):
    can_remove_records_from_community = [
        SystemProcess(),
        CommunityRolePermittedInCF(community_permission_name="can_remove_records_from_community"),
    ]
