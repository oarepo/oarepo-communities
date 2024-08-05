from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityNotIncludedException, PrimaryCommunityException
from ..resolvers.communities import CommunityRoleObj
from ..utils import get_associated_service, resolve_community


class CommunityRemoveSecondaryAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        community = self.request.receiver.resolve()
        community = resolve_community(community)
        service = get_record_service_for_record(topic)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.remove(topic, str(community.id), uow=uow)


# Request
#
class RemoveSecondaryRequestType(OARepoRequestType):
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
            "accept": CommunityRemoveSecondaryAcceptAction,
        }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = (
            CommunityRoleObj.community_role_or_community_ref_get_community_id(
                list(receiver.values())[0]
            )
        )
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
