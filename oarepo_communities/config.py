from oarepo_communities.requests.migration import CommunityMigrationRequestType
from oarepo_communities.requests.remove_secondary import RemoveSecondaryRequestType
from oarepo_communities.requests.submission_secondary import (
    SecondaryCommunitySubmissionRequestType,
)
from oarepo_communities.resolvers.communities import CommunityRoleResolver
from oarepo_communities.resolvers.ui import (
    CommunityRoleUIResolver,
    OARepoCommunityReferenceUIResolver,
)

REQUESTS_REGISTERED_TYPES = [
    CommunityMigrationRequestType(),
    RemoveSecondaryRequestType(),
    SecondaryCommunitySubmissionRequestType(),
]

REQUESTS_ALLOWED_RECEIVERS = ["community", "community_role"]

REQUESTS_ENTITY_RESOLVERS = [
    CommunityRoleResolver(),
]

ENTITY_REFERENCE_UI_RESOLVERS = {
    "community": OARepoCommunityReferenceUIResolver("community"),
    "community_role": CommunityRoleUIResolver("community_role"),
}
