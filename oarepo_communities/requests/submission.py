from flask_babelex import lazy_gettext as _
from invenio_records_resources.services.uow import RecordCommitOp, RecordIndexOp
from invenio_requests.customizations import RequestType, actions
from invenio_access.permissions import system_identity

from ..services.errors import CommunityAlreadyExists, OpenRequestAlreadyExists
from ..services.record_communities.service import include_record_in_community
from ..utils.utils import get_matching_service, _exists


#
# Actions
#
class SubmitAction(actions.SubmitAction):
    """Submit action."""

    def can_execute(self):
        community = self.request.receiver.resolve()
        record = self.request.topic.resolve()
        id_ = str(community.id)
        already_included = id_ in record.parent.communities
        if already_included:
            return False

        existing_request_id = _exists(system_identity, id_, record, self.request.type.type_id)
        if existing_request_id:
            return False

        return True

class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        community = self.request.receiver.resolve()
        service = get_matching_service(record)

        record.parent.community_submission = None

        default = self.request.type.set_as_default
        include_record_in_community(record, community, service, uow, default)

        super().execute(identity, uow)


class DeclineAction(actions.DeclineAction):
    """Decline action."""

    def execute(self, identity, uow):
        """Execute action."""
        # Keeps the record and the review connected so the user can see the
        # outcome of the request
        # The receiver (curator) won't have access anymore to the draft
        # The creator (uploader) should still have access to the record/draft
        draft = self.request.topic.resolve()
        service = get_matching_service(draft)
        super().execute(identity, uow)

        # TODO: this shouldn't be required BUT because of the caching mechanism
        # in the review systemfield, the review should be set with the updated
        # request object
        draft.parent.review = self.request
        uow.register(RecordCommitOp(draft.parent))
        # update draft to reflect the new status
        uow.register(RecordIndexOp(draft, indexer=service.indexer))


class CancelAction(actions.CancelAction):
    """Decline action."""

    def execute(self, identity, uow):
        """Execute action."""
        # Remove draft from request
        # Same reasoning as in 'decline'
        draft = self.request.topic.resolve()
        service = get_matching_service(draft)
        draft.parent.review = None
        uow.register(RecordCommitOp(draft.parent))
        # update draft to reflect the new status
        uow.register(RecordIndexOp(draft, indexer=service.indexer))
        super().execute(identity, uow)


class ExpireAction(actions.ExpireAction):
    """Expire action."""

    def execute(self, identity, uow):
        """Execute action."""
        # Same reasoning as in 'decline'
        draft = self.request.topic.resolve()
        service = get_matching_service(draft)

        # TODO: What more to do? simply close the request? Similarly to
        # decline, how does a user resubmits the request to the same community.
        super().execute(identity, uow)

        # TODO: this shouldn't be required BUT because of the caching mechanism
        # in the review systemfield, the review should be set with the updated
        # request object
        draft.parent.review = self.request
        uow.register(RecordCommitOp(draft.parent))
        # update draft to reflect the new status
        uow.register(RecordIndexOp(draft, indexer=service.indexer))


#
# Request
#
class CommunitySubmission(RequestType):
    """Review request for submitting a record to a community."""

    type_id = "community-submission"
    name = _("Community submission")

    block_publish = True
    set_as_default = True

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["community"]
    allowed_topic_ref_types = ["record"]
    needs_context = {
        "community_roles": ["owner", "manager", "curator"],
    }

    available_actions = {
        "create": actions.CreateAction,
        "submit": SubmitAction,
        "delete": actions.DeleteAction,
        "accept": AcceptAction,
        "decline": DeclineAction,
        "cancel": CancelAction,
        "expire": ExpireAction,
    }
