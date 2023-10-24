from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)

from .record import RecordCommunitiesGenerator


class CommunityPermissionPolicy(RecordPermissionPolicy):
    can_search = [SystemProcess(), AnyUser()]
    can_read = [SystemProcess(), RecordCommunitiesGenerator("can_read")]
    can_create = [SystemProcess(), AuthenticatedUser()]
    can_update = [SystemProcess(), RecordCommunitiesGenerator("can_update")]
    can_delete = [SystemProcess(), RecordCommunitiesGenerator("can_delete")]
    can_manage = [SystemProcess()]

    can_create_files = [SystemProcess()]
    can_set_content_files = [SystemProcess()]
    can_get_content_files = [AnyUser(), SystemProcess()]
    can_commit_files = [SystemProcess()]
    can_read_files = [AnyUser(), SystemProcess()]
    can_update_files = [SystemProcess()]
    can_delete_files = [SystemProcess()]

    can_edit = [SystemProcess()]
    can_new_version = [SystemProcess()]
    can_search_drafts = [SystemProcess()]
    can_read_draft = [SystemProcess()]
    can_update_draft = [SystemProcess()]
    can_delete_draft = [SystemProcess()]
    can_publish = [SystemProcess(), RecordCommunitiesGenerator("can_publish")]
    can_draft_create_files = [SystemProcess()]
    can_draft_set_content_files = [SystemProcess()]
    can_draft_get_content_files = [SystemProcess()]
    can_draft_commit_files = [SystemProcess()]
    can_draft_read_files = [SystemProcess()]
    can_draft_update_files = [SystemProcess()]

    can_add_community = [SystemProcess(), AuthenticatedUser()]
    can_remove_community = [SystemProcess(), AuthenticatedUser()]
