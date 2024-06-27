from oarepo_requests.utils import get_matching_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..utils.utils import get_associated_service
from . import submission
from .submission import AbstractCommunitySubmissionRequestType


class AcceptAction(submission.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        # todo what if it's already removed?
        service = get_matching_service_for_record(record)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.remove(
            record, str(record.parent.communities.default.id), uow=uow
        )
        super().execute(identity, uow)


class CommunityMigrationRequestType(AbstractCommunitySubmissionRequestType):
    """Review request for submitting a record to a community."""

    type_id = "community-migration"
    name = _("Community-migration")

    set_as_default = True

    available_actions = {
        **AbstractCommunitySubmissionRequestType.available_actions,
        "accept": AcceptAction,
    }
