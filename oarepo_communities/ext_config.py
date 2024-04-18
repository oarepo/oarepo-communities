from oarepo_communities.permissions.presets import (
    CommunityPermissionPolicy,
    CommunityRecordsCommunityPermissionPolicy,
    CommunityRecordsEveryonePermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "community": CommunityPermissionPolicy,
    "community-records-community": CommunityRecordsCommunityPermissionPolicy,
    "community-records-everyone": CommunityRecordsEveryonePermissionPolicy,
}
