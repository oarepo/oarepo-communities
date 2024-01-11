from invenio_access.permissions import system_identity
from oarepo_requests.actions.publish_draft import PublishDraftAcceptAction, publish_draft
from oarepo_requests.types.publish_draft import PublishDraftRequestType
from invenio_requests.proxies import current_requests_service

class CommunityPublishDraftAcceptAction(PublishDraftAcceptAction):
    def execute(self, identity, uow):
        super().execute(system_identity, uow) # the permission is resolved in execute action method of requests service


class CommunityPublishDraftRequestType(PublishDraftRequestType):
    allowed_receiver_ref_types = ["oarepo_community"]

    needs_context = {"community_permission_name": "can_publish_request"}

    available_actions = {
        **PublishDraftRequestType.available_actions,
        "accept": CommunityPublishDraftAcceptAction,
    }
