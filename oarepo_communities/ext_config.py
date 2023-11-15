from oarepo_communities.permissions.presets import (
    CommunityPermissionPolicy,
    CommunityRecordsCommunityPermissionPolicy,
    CommunityRecordsEveryonePermissionPolicy,
    RecordCommunitiesCommunityPermissionPolicy,
    RecordCommunitiesEveryonePermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "community": CommunityPermissionPolicy,
    "record-communities-community": RecordCommunitiesCommunityPermissionPolicy,
    "community-records-community": CommunityRecordsCommunityPermissionPolicy,
    "record-communities-everyone": RecordCommunitiesEveryonePermissionPolicy,
    "community-records-everyone": CommunityRecordsEveryonePermissionPolicy,
}
