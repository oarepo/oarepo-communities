from flask_babelex import lazy_gettext as _
from invenio_access.permissions import system_identity
from invenio_requests.customizations import RequestType
from invenio_requests.customizations import actions
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_requests.utils import get_matching_service, request_exists, resolve_reference_dict, open_request_exists

from ..errors import CommunityAlreadyIncludedException
from ..services.record_communities.service import include_record_in_community


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        community = self.request.receiver.resolve()
        service = get_matching_service(record)
        include_record_in_community(record, community, service, uow, default=self.request.type.set_as_default)

        super().execute(identity, uow)


# Request
#

class CommunitySubmissionRequestType(OARepoRequestType):
    """Review request for submitting a record to a community."""

    type_id = "community_submission"
    name = _("Community submission")

    block_publish = True
    set_as_default = True

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["oarepo_community"]
    allowed_topic_ref_types = ["record"]

    needs_context = {"community_permission_name": "can_submit_to_community"}

    available_actions = {
        **OARepoRequestType.available_actions,
        "accept": AcceptAction,
    }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        receiver_community_id = list(receiver.values())[0]
        topic = resolve_reference_dict(topic)
        already_included = receiver_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException
        #open_request_exists(topic, self.type_id)
