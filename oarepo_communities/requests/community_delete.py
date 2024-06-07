from oarepo_requests.actions.delete_topic import DeleteTopicAcceptAction
from oarepo_requests.types.delete_record import DeleteRecordRequestType

from oarepo_communities.permissions.identity import RequestIdentity


class CommunityDeleteTopicAcceptAction(DeleteTopicAcceptAction):
    def execute(self, identity, uow, *args, **kwargs):
        identity = RequestIdentity(identity)
        super().execute(
            identity, uow, *args, **kwargs
        )  # the permission is resolved in execute action method of requests service


class CommunityDeleteRecordRequestType(DeleteRecordRequestType):
    allowed_receiver_ref_types = ["community"]

    available_actions = {
        **DeleteRecordRequestType.available_actions,
        "accept": CommunityDeleteTopicAcceptAction,
    }
