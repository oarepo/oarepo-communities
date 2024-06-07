from oarepo_requests.utils import get_matching_service_for_record

from ..utils.utils import get_associated_service
from . import submission
from .submission import CommunitySubmissionRequestType


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


class CommunityMigrationRequestType(CommunitySubmissionRequestType):
    """Review request for submitting a record to a community."""

    type_id = "community_migration"
    name = "Community-migration"

    available_actions = {
        **CommunitySubmissionRequestType.available_actions,
        "accept": AcceptAction,
    }
