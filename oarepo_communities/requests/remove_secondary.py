from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityNotIncludedException, PrimaryCommunityException
from ..proxies import current_oarepo_communities


class RemoveSecondaryCommunityAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        community_id = self.request.receiver.resolve().community_id
        service = get_record_service_for_record(topic)
        community_inclusion_service = (
            current_oarepo_communities.community_inclusion_service
        )
        community_inclusion_service.remove(
            topic, community_id, record_service=service, uow=uow
        )


# Request
#
class RemoveSecondaryCommunityRequestType(OARepoRequestType):
    """Review request for submitting a record to a community."""

    type_id = "remove_secondary_community"
    name = _("Remove secondary community")

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": RemoveSecondaryCommunityAcceptAction,
        }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data["payload"]["community"]
        not_included = target_community_id not in topic.parent.communities.ids
        if not_included:
            raise CommunityNotIncludedException(
                "Cannot remove, record is not in this community."
            )
        if target_community_id == str(topic.parent.communities.default.id):
            raise PrimaryCommunityException("Cannot remove record's primary community.")

    @classmethod
    def can_possibly_create(self, identity, topic, *args, **kwargs):
        super().can_possibly_create(identity, topic, *args, **kwargs)
        try:
            communities = topic.parent.communities.ids
        except AttributeError:
            return False
        return len(communities) > 1
