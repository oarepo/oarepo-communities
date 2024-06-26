from flask_babelex import lazy_gettext as _
from invenio_requests.customizations import actions
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_requests.utils import get_matching_service_for_record

from ..errors import CommunityAlreadyIncludedException
from ..utils.utils import get_associated_service


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        community = self.request.receiver.resolve()
        service = get_matching_service_for_record(record)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.include(
            record, community, uow=uow, default=self.request.type.set_as_default
        )

        super().execute(identity, uow)


# Request
#


class AbstractCommunitySubmissionRequestType(OARepoRequestType):  # rename abstract

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    available_actions = {
        **OARepoRequestType.available_actions,
        "accept": AcceptAction,
    }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = list(receiver.values())[0]
        already_included = receiver_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException
        # open_request_exists(topic, self.type_id)
