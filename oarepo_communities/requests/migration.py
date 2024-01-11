import marshmallow as ma

from ..services.record_communities.service import remove
from . import submission
from .submission import CommunitySubmissionRequestType


class AcceptAction(submission.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        # todo what if it's already removed?
        # todo move to service method?
        remove(str(record.parent.communities.default.id), record)
        super().execute(identity, uow)


class CommunityMigrationRequestType(CommunitySubmissionRequestType):
    """Review request for submitting a record to a community."""

    type_id = "community_migration"
    name = "Community-migration"

    available_actions = {
        **CommunitySubmissionRequestType.available_actions,
        "accept": AcceptAction,
    }

    needs_context = {"community_permission_name": "can_submit_to_community"}
