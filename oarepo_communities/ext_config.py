from oarepo_communities.permissions.presets import (
    CommunitiesEveryonePermissionPolicy,
    CommunitiesFromCFPermissionPolicy,
    CommunityPermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "community": CommunityPermissionPolicy,
    "communities-everyone": CommunitiesEveryonePermissionPolicy,
    "communities-from-cf": CommunitiesFromCFPermissionPolicy,
}
