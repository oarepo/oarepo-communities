from . import submission
from .submission import CommunitySubmission


from ..services.record_communities.service import remove
import marshmallow as ma

class AcceptAction(submission.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        payload = self.request["payload"]
        remove(payload["community"], record)
        super().execute(identity, uow)

class CommunityMigration(CommunitySubmission):
    """Review request for submitting a record to a community."""

    type_id = "community-migration"
    name = "Community-migration"

    available_actions = {
        **CommunitySubmission.available_actions,
        "accept": AcceptAction,
    }

    payload_schema = {
        "community": ma.fields.String()
    }
