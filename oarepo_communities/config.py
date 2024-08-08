from oarepo_communities.requests.migration import (
    ConfirmCommunityMigrationRequestType,
    InitiateCommunityMigrationRequestType,
)
from oarepo_communities.requests.remove_secondary import (
    RemoveSecondaryCommunityRequestType,
)
from oarepo_communities.requests.submission_secondary import (
    SecondaryCommunitySubmissionRequestType,
)
from oarepo_communities.resolvers.ui import CommunityRoleUIResolver
from oarepo_communities.services.custom_fields.workflow import WorkflowCF

REQUESTS_REGISTERED_TYPES = [
    InitiateCommunityMigrationRequestType(),
    ConfirmCommunityMigrationRequestType(),
    RemoveSecondaryCommunityRequestType(),
    SecondaryCommunitySubmissionRequestType(),
]

REQUESTS_ALLOWED_RECEIVERS = ["community", "community_role"]

ENTITY_REFERENCE_UI_RESOLVERS = {
    "community_role": CommunityRoleUIResolver("community_role"),
}

DEFAULT_COMMUNITIES_CUSTOM_FIELDS = [WorkflowCF(name="workflow")]
