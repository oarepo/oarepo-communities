from invenio_requests.customizations import actions
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_requests.utils import get_matching_service_for_record, resolve_reference_dict

from ..errors import CommunityNotIncludedException, PrimaryCommunityException
from ..utils.utils import get_associated_service


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        community = self.request.receiver.resolve()
        service = get_matching_service_for_record(record)
        record_communities_service = get_associated_service(
            service, "service_record_communities"
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
    allowed_receiver_ref_types = ["oarepo_community"]
    allowed_topic_ref_types = ["record"]

    needs_context = {"community_permission_name": "can_remove_secondary_community"}

    available_actions = {
        **OARepoRequestType.available_actions,
        "accept": AcceptAction,
    }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = list(receiver.values())[0]
        topic_obj = resolve_reference_dict(topic)
        not_included = receiver_community_id not in topic_obj.parent.communities
        if not_included:
            raise CommunityNotIncludedException
        if receiver_community_id == str(topic_obj.parent.communities.default.id):
            raise PrimaryCommunityException
