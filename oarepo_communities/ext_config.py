from oarepo_communities.permissions.presets import (
    CommunityPermissionPolicy,
    CommunityRecordsCommunityPermissionPolicy,
    CommunityRecordsEveryonePermissionPolicy,
    RecordCommunitiesEveryonePermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "community": CommunityPermissionPolicy,
    "community-records-community": CommunityRecordsCommunityPermissionPolicy,
    "record-communities-everyone": RecordCommunitiesEveryonePermissionPolicy,
    "community-records-everyone": CommunityRecordsEveryonePermissionPolicy,
}
