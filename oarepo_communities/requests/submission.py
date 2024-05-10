from flask_babelex import lazy_gettext as _
from invenio_requests.customizations import actions
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_requests.utils import (
    get_matching_service_for_record,
    resolve_reference_dict,
)

from ..errors import CommunityAlreadyIncludedException
from ..utils.utils import get_associated_service


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        record = self.request.topic.resolve()
        community = self.request.receiver.resolve()
        service = get_matching_service_for_record(record)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.include(
            record, community, uow=uow, default=self.request.type.set_as_default
        )

        super().execute(identity, uow)


# Request
#


class CommunitySubmissionRequestType(OARepoRequestType):  # rename abstract
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
        # open_request_exists(topic, self.type_id)
