from __future__ import annotations


from typing import TYPE_CHECKING

from oarepo_requests.actions.generic import OARepoAcceptAction, RequestActionState
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

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_records_resources.services.uow import UnitOfWork
    from invenio_requests.customizations import RequestType
    from invenio_requests.customizations.actions import RequestAction
    from oarepo_requests.typing import EntityReference


from typing import TYPE_CHECKING, Any
from typing_extensions import override

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_drafts_resources.records import Record
    from invenio_requests.records.api import Request


class CommunitySubmissionAcceptAction(OARepoAcceptAction):
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # it seems that the safest way is to just get the community id from the request payload?
        topic = state.topic
        community_id = self.request.get("payload", {}).get("community", None)
        if not community_id:
            raise TargetCommunityNotProvidedException("Target community not provided.")
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
    def available_actions(cls) -> dict[str, type[RequestAction]]:
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
            return _("Add to secondary community")
        match request.status:
            case "submitted":
                return _("Confirm record secondary community submission")
            case _:
                return _("Request record secondary community submission")

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
        if not request:
            return _(
                "After submitting record secondary community submission request, it will first have to be approved by responsible person(s) of the target community. "
                "You will be notified about the decision by email."
            )
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "Record secondary community submission request has been submitted. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "User has requested to add secondary community to a record. "
                        "You can now accept or decline the request."
                    )
                return _(
                    "Record secondary community submission request has been submitted."
                )
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to add record to secondary community.")

                return _("Request not yet submitted.")

    def can_create(
        self,
        identity: Identity,
        data: dict,
        receiver: EntityReference,
        topic: Record,
        creator: EntityReference,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data.get("payload", {}).get("community", None)
        if not target_community_id:
            raise TargetCommunityNotProvidedException("Target community not provided.")

        already_included = target_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException(
                "Record is already included in this community."
            )
