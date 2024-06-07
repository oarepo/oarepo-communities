from invenio_requests.customizations import actions
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_requests.utils import get_matching_service_for_record

from ..errors import CommunityNotIncludedException, PrimaryCommunityException
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
        record_communities_service.remove(record, str(community.id), uow=uow)

        super().execute(identity, uow)


# Request
#
class RemoveSecondaryRequestType(OARepoRequestType):
    """Review request for submitting a record to a community."""

    type_id = "remove_secondary_community"

    block_publish = True
    set_as_default = True

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["community"]
    allowed_topic_ref_types = ["record"]


    available_actions = {
        **OARepoRequestType.available_actions,
        "accept": AcceptAction,
    }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = list(receiver.values())[0]
        not_included = receiver_community_id not in topic.parent.communities
        if not_included:
            raise CommunityNotIncludedException
        if receiver_community_id == str(topic.parent.communities.default.id):
            raise PrimaryCommunityException

    @classmethod
    def can_possibly_create(self, identity, topic, *args, **kwargs):
        super().can_possibly_create(identity, topic, *args, **kwargs)
        try:
            communities = topic.parent.communities.ids
        except AttributeError:
            return False
        return len(communities) > 1
