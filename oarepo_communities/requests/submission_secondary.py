from __future__ import annotations

from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _
import marshmallow as ma

from oarepo_requests.utils import (
    request_identity_matches,
)

from ..errors import (
    CommunityAlreadyIncludedException,
    TargetCommunityNotProvidedException,
)
from ..proxies import current_oarepo_communities


from typing import TYPE_CHECKING, Any
from typing_extensions import override

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_drafts_resources.records import Record
    from invenio_requests.records.api import Request


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
            "readOnlyLabel": _("Secondary community:"),
        },
    }

    @override
    def stateful_name(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
        # This check fails when target community is involved, as it simply does not know the target community at this point
        # if is_auto_approved(self, identity=identity, topic=topic):
        #     return _("Add secondary community")
        if not request:
            return _("Initiate secondary community submission")
        match request.status:
            case "submitted":
                return _("Confirm secondary community submission")
            case _:
                return _("Request secondary community submission")

    @override
    def stateful_description(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful description of the request."""
        # This check fails when target community is involved, as it simply does not know the target community at this point
        # if is_auto_approved(self, identity=identity, topic=topic):
        #     return _("Click to immediately tie the record to another community.")

        if not request:
            return _(
                "After you submit secondary community submission request, it will first have to be approved by curators/owners of the target community. "
                "You will be notified about the decision by email."
            )
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "The secondary community submission request has been submitted. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "User has requested to add secondary community to a record. "
                        "You can now accept or decline the request."
                    )
                return _("Secondary community submission request has been submitted.")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to initiate secondary community submission.")

                return _("Request not yet submitted.")

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data.get("payload", {}).get("community", None)
        if not target_community_id:
            raise TargetCommunityNotProvidedException("Target community not provided.")

        already_included = target_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException(
                "Record is already included in this community."
            )
