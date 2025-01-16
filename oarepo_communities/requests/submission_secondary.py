from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _
import marshmallow as ma

from ..errors import (
    CommunityAlreadyIncludedException,
    TargetCommunityNotProvidedException,
)
from ..proxies import current_oarepo_communities


class CommunitySubmissionAcceptAction(OARepoAcceptAction):
    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        community_id, role = (
            self.request.receiver.resolve().entities[0]._parse_ref_dict()
        )
        service = get_record_service_for_record(topic)
        community_inclusion_service = (
            current_oarepo_communities.community_inclusion_service
        )
        community_inclusion_service.include(
            topic, community_id, record_service=service, uow=uow, default=False
        )


class SecondaryCommunitySubmissionRequestType(NonDuplicableOARepoRequestType):
    """Review request for submitting a record to a community."""

    type_id = "secondary_community_submission"
    name = _("Secondary community submission")
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
    editable = False

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": CommunitySubmissionAcceptAction,
        }

    topic_can_be_none = False
    payload_schema = {
        "community": ma.fields.String(required=True),
    }

    form = {
        "field": "community",
        "ui_widget": "SecondaryCommunitySelector",
        "read_only_ui_widget": "SelectedTargetCommunity",
        "props": {
            "requestType": "secondary_community_submission",
        },
    }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        print("can_create", flush=True)
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data.get("payload", {}).get("community", None)
        print("target_community_id", target_community_id, flush=True)
        if not target_community_id:
            raise TargetCommunityNotProvidedException("Target community not provided.")

        already_included = target_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException(
                "Record is already included in this community."
            )
