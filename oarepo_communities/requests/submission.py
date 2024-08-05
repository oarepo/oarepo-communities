from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from ..errors import CommunityAlreadyIncludedException
from ..resolvers.communities import CommunityRoleObj
from ..utils import get_associated_service, resolve_community


class CommunitySubmissionAcceptAction(OARepoAcceptAction):

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        if "community" not in kwargs:
            community = self.request.receiver.resolve()
            community = resolve_community(
                community
            )  # resolve receiver, can be either community or community_role
        else:
            community = kwargs["community"]
        service = get_record_service_for_record(topic)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.include(
            topic, community, uow=uow, default=self.request.type.set_as_default
        )


class AbstractCommunitySubmissionRequestType(OARepoRequestType):  # rename abstract

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": CommunitySubmissionAcceptAction,
        }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = (
            CommunityRoleObj.community_role_or_community_ref_get_community_id(
                list(receiver.values())[0]
            )
        )
        already_included = receiver_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException
