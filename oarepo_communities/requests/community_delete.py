from oarepo_requests.actions.delete_topic import DeleteTopicAcceptAction
from oarepo_requests.types.delete_record import DeleteRecordRequestType


class CommunityDeleteTopicAcceptAction(DeleteTopicAcceptAction):
    def execute(self, identity, uow, *args, **kwargs):
        super().execute(
            identity, uow, *args, is_request=True, **kwargs
        )  # the permission is resolved in execute action method of requests service


class CommunityDeleteRecordRequestType(DeleteRecordRequestType):
    allowed_receiver_ref_types = ["community"]

    needs_context = {"community_permission_name": "can_delete_request"}

    available_actions = {
        **DeleteRecordRequestType.available_actions,
        "accept": CommunityDeleteTopicAcceptAction,
    }
