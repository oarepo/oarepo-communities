from oarepo_requests.actions.publish_draft import PublishDraftAcceptAction
from oarepo_requests.types.publish_draft import PublishDraftRequestType


class CommunityPublishDraftAcceptAction(PublishDraftAcceptAction):
    def execute(self, identity, uow, *args, **kwargs):
        super().execute(
            identity, uow, *args, is_request=True, **kwargs
        )  # the permission is resolved in execute action method of requests service


class CommunityPublishDraftRequestType(PublishDraftRequestType):
    allowed_receiver_ref_types = ["community"]

    needs_context = {"community_permission_name": "can_publish_request"}

    available_actions = {
        **PublishDraftRequestType.available_actions,
        "accept": CommunityPublishDraftAcceptAction,
    }
