from oarepo_communities.permissions.presets import CommunityPermissionPolicy, CommunitiesEveryonePermissionPolicy, CommunitiesFromCFPermissionPolicy

OAREPO_PERMISSIONS_PRESETS = {
    "community": CommunityPermissionPolicy,
    "communities-everyone": CommunitiesEveryonePermissionPolicy,
    "communities-from-cf": CommunitiesFromCFPermissionPolicy,
}
