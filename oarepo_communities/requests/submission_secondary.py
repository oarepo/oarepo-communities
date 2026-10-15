#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Request type for submitting a record to a secondary community."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import marshmallow as ma
from invenio_communities.communities.records.api import Community
from invenio_drafts_resources.records.api import Record as RecordWithParent
from invenio_i18n import lazy_gettext as _
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types.generic import NonDuplicableOARepoRecordRequestType
from oarepo_requests.utils import (
    classproperty,
)

from ..errors import (
    CommunityAlreadyIncludedError,
    TargetCommunityNotProvidedError,
)
from .utils import (
    add_record_to_community,
    no_request_message,
    on_request_creator,
    on_request_submitted,
    on_request_submitted_creator,
    on_request_submitted_receiver,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_records_resources.records import Record
    from invenio_requests.customizations.actions import RequestAction


from typing import TYPE_CHECKING, Any, override

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_drafts_resources.records import Record
    from invenio_requests.records.api import Request


class CommunitySubmissionAcceptAction(OARepoAcceptAction):
    """Accept action for submission to a secondary community."""

    @override
    def apply(
        self,
        identity: Identity,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # it seems that the safest way is to just get the community id from the request payload?
        community_id = self.request.get("payload", {}).get("community", None)
        if not community_id:
            raise TargetCommunityNotProvidedError("Target community not provided.")
        community = Community.get_record(community_id)
        add_record_to_community(cast("RecordWithParent", self.topic), community, self.request, uow)


class SecondaryCommunitySubmissionRequestType(NonDuplicableOARepoRecordRequestType):
    """Review request for submitting a record to a community."""

    type_id = "secondary_community_submission"
    name = _("Secondary community submission")
    editable = False

    topic_can_be_none = False
    payload_schema: Mapping[str, ma.fields.Field] = {  # type: ignore[assignment]
        "community": ma.fields.String(required=True),
    }

    @classproperty
    @override
    def available_actions(  # type: ignore[override]
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": CommunitySubmissionAcceptAction,
        }

    form: Mapping[str, Any] = {
        "field": "community",
        "ui_widget": "SecondaryCommunitySelector",
        "read_only_ui_widget": "SelectedTargetCommunity",
        "props": {
            "requestType": "secondary_community_submission",
            "readOnlyLabel": _("Secondary community:"),
        },
    }

    @override
    @no_request_message(_("Add to secondary community"))
    @on_request_submitted(_("Confirm record secondary community submission"))
    def stateful_name(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
        return _("Request record secondary community submission")

    @override
    @no_request_message(
        _(
            "After submitting record secondary community submission request, "
            "it will first have to be approved by responsible person(s) of the target community. "
            "You will be notified about the decision by email."
        )
    )
    @on_request_submitted_creator(
        _(
            "Record secondary community submission request has been submitted. "
            "You will be notified about the decision by email."
        )
    )
    @on_request_submitted_receiver(
        _("User has requested to add secondary community to a record. You can now accept or decline the request.")
    )
    @on_request_submitted(_("Record secondary community submission request has been submitted."))
    @on_request_creator(_("Submit to add record to secondary community."))
    def stateful_description(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful description of the request."""
        return _("Request not yet submitted.")

    @override
    def can_create(
        self,
        identity: Identity,
        data: dict,
        receiver: dict[str, str],
        topic: Record,
        creator: dict[str, str],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data.get("payload", {}).get("community", None)
        if not target_community_id:
            raise TargetCommunityNotProvidedError("Target community not provided.")

        if not isinstance(topic, RecordWithParent):
            raise TypeError("Topic must be a RecordWithParent instance.")

        already_included = target_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedError("Record is already included in this community.")
