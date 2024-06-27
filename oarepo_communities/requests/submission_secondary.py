from oarepo_requests.types import ModelRefTypes
from oarepo_runtime.i18n import lazy_gettext as _

from oarepo_communities.requests.submission import (
    AbstractCommunitySubmissionRequestType,
)


class SecondaryCommunitySubmissionRequestType(AbstractCommunitySubmissionRequestType):
    """Review request for submitting a record to a community."""

    type_id = "secondary-community-submission"
    name = _("Secondary community submission")

    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    set_as_default = False
