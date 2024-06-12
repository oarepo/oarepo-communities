from oarepo_requests.actions.publish_draft import PublishDraftAcceptAction
from oarepo_requests.types.publish_draft import PublishDraftRequestType

from oarepo_communities.permissions.identity import RequestIdentity
from oarepo_communities.requests.actions import (
    StatusChangingDeclineAction,
    StatusChangingSubmitAction,
)


class CommunityPublishDraftAcceptAction(PublishDraftAcceptAction):
    def execute(self, identity, uow, *args, **kwargs):
        identity = RequestIdentity(identity)
        super().execute(
            identity, uow, *args, **kwargs
        )  # the permission is resolved in execute action method of requests service


class CommunityPublishDraftRequestType(PublishDraftRequestType):
    allowed_receiver_ref_types = ["community"]

    available_actions = {
        **PublishDraftRequestType.available_actions,
        "submit": StatusChangingSubmitAction,
        "decline": StatusChangingDeclineAction,
        "accept": CommunityPublishDraftAcceptAction,
    }
