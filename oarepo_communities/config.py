from oarepo_communities.requests.migration import (
    ConfirmCommunityMigrationRequestType,
    InitiateCommunityMigrationRequestType,
)
from oarepo_communities.requests.remove_secondary import RemoveSecondaryRequestType
from oarepo_communities.requests.submission_secondary import (
    SecondaryCommunitySubmissionRequestType,
)
from oarepo_communities.resolvers.ui import (
    CommunityRoleUIResolver,
    OARepoCommunityReferenceUIResolver,
)

REQUESTS_REGISTERED_TYPES = [
    InitiateCommunityMigrationRequestType(),
    ConfirmCommunityMigrationRequestType(),
    RemoveSecondaryRequestType(),
    SecondaryCommunitySubmissionRequestType(),
]

REQUESTS_ALLOWED_RECEIVERS = ["community", "community_role"]

ENTITY_REFERENCE_UI_RESOLVERS = {
    "community": OARepoCommunityReferenceUIResolver("community"),
    "community_role": CommunityRoleUIResolver("community_role"),
}
