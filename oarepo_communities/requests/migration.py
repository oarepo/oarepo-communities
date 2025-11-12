#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Migration requests for communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import marshmallow as ma
from flask import g
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_drafts_resources.records.api import Record as RecordWithParent
from invenio_i18n import lazy_gettext as _
from invenio_notifications.services.uow import NotificationOp
from invenio_rdm_records.notifications.builders import (
    CommunityInclusionAcceptNotificationBuilder,
)
from invenio_rdm_records.requests.community_inclusion import is_access_restriction_valid
from invenio_rdm_records.services.errors import InvalidAccessRestrictions
from invenio_requests.customizations.actions import RequestAction
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.proxies import current_requests_service
from oarepo_requests.types.generic import NonDuplicableOARepoRecordRequestType
from oarepo_requests.utils import (
    classproperty,
    open_request_exists,
)

from oarepo_communities.ui.allowed_communities import AllowedCommunitiesComponent
from oarepo_communities.utils import community_to_dict

from ..errors import (
    CommunityAlreadyIncludedError,
    TargetCommunityNotProvidedError,
)
from .utils import (
    auto_approved_message,
    change_primary_community,
    no_request_message,
    on_request_creator,
    on_request_submitted,
    on_request_submitted_creator,
    on_request_submitted_receiver,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_records_resources.records import Record
    from invenio_requests.records.api import Request


class InitiateCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Source community accepting the initiate request autocreates confirm request delegated to the target community."""

    @override
    def apply(
        self,
        identity: Identity,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        request_item = current_requests_service.create(
            system_identity,
            data={"payload": self.request.get("payload", {})},
            request_type=ConfirmCommunityMigrationRequestType.type_id,
            topic=self.topic,
            # not sure about whether this is always available
            # self.request.created_by.resolve() should always work but breaks (probably incorrect) typing
            creator=self.request["created_by"],
            uow=uow,
            **kwargs,
        )
        current_requests_service.execute_action(system_identity, request_item.id, "submit", uow=uow)


class ConfirmCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Accept action."""

    @override
    def apply(
        self,
        identity: Identity,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?

        community_id = self.request.get("payload", {}).get("community", None)
        if not community_id:
            raise TargetCommunityNotProvidedError("Target community not provided.")
        community = cast("Community", Community.pid.resolve(community_id))

        if not is_access_restriction_valid(self.topic, community):  # type: ignore[reportArgumentType]
            raise InvalidAccessRestrictions("Invalid access restrictions between target community and record.")

        change_primary_community(cast("RecordWithParent", self.topic), community, self.request, uow)

        if kwargs.get("send_notification", True):
            uow.register(
                NotificationOp(
                    CommunityInclusionAcceptNotificationBuilder.build(identity=identity, request=self.request)
                )
            )


class InitiateCommunityMigrationRequestType(NonDuplicableOARepoRecordRequestType):
    """Request which is used to start migrating record from one primary community to another one.

    The recipient of this request type should be the community role of the current
    primary community, that is the owner of the current community must agree that
    the record could be migrated elsewhere.
    When this request is accepted, a new request of type
    ConfirmCommunityMigrationRequestType should be created and
    submitted to perform the community migration.
    """

    type_id = "initiate_community_migration"
    name = _("Inititiate Community migration")

    description = _("Move record to another primary community.")  # type: ignore[reportAssignmentType]

    editable = False
    topic_can_be_none = False
    payload_schema: Mapping[str, ma.fields.Field] | None = {
        "community": ma.fields.String(),
    }
    receiver_can_be_none = True

    @classproperty
    @override
    def available_actions(  # type: ignore[override]
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": InitiateCommunityMigrationAcceptAction,
        }

    @classmethod
    def is_applicable_to(cls, identity: Identity, topic: Record, *args: Any, **kwargs: Any) -> bool:
        """Check if the request type is applicable to the topic."""
        if open_request_exists(topic, cls.type_id) or open_request_exists(
            topic, ConfirmCommunityMigrationRequestType.type_id
        ):
            return False
        # check if the user has more than one community to which they can migrate
        allowed_communities_count = 0
        for __ in AllowedCommunitiesComponent.get_allowed_communities(identity, "create"):
            allowed_communities_count += 1
            if allowed_communities_count > 1:
                break

        if allowed_communities_count <= 1:
            return False

        return super().is_applicable_to(identity, topic, *args, **kwargs)  # type: ignore[no-any-return]

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
            raise TypeError("Topic must be a draft record.")
        already_included = target_community_id == str(topic.parent.communities.default.id)
        if already_included:
            raise CommunityAlreadyIncludedError("Already inside this primary community.")

    @override
    @auto_approved_message(_("Inititiate record community migration"))
    @no_request_message(_("Inititiate record community migration"))
    @on_request_submitted(_("Record community migration initiated"))
    def stateful_name(  # type: ignore[override]
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
        return _("Request record community migration")

    @override
    @auto_approved_message(
        _(
            "Click to immediately start record migration. "
            "After submitting the request will immediatelly be forwarded "
            "to responsible person(s) in the target community. "
            "You will be notified about the decision by email."
        )
    )
    @no_request_message(
        _(
            "After you submit record community migration request, "
            "it will first have to be approved by responsible person(s) of the current community. "
            "Then it will have to be accepted by responsible persons(s) of the target community. "
            "You will be notified about the decision by email."
        )
    )
    @on_request_submitted_creator(
        _("Record community migration request has been submitted. You will be notified about the decision by email.")
    )
    @on_request_submitted_receiver(
        _("User has requested record community migration. You can now accept or decline the request.")
    )
    @on_request_submitted(_("Record community migration request has been submitted."))
    @on_request_creator(_("Submit to initiate record community migration. "))
    def stateful_description(  # type: ignore[override]
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful description of the request."""
        return _("Request not yet submitted.")

    @property
    def form(self) -> dict[str, Any]:
        """Form configuration for request form."""
        allowed_communities = AllowedCommunitiesComponent.get_allowed_communities(g.identity, "create")
        serialized_allowed_communities = [community_to_dict(community) for community in allowed_communities]
        return {
            "field": "community",
            "ui_widget": "TargetCommunitySelector",
            "read_only_ui_widget": "SelectedTargetCommunity",
            "props": {
                "readOnlyLabel": _("Target community:"),
                "allowedCommunities": serialized_allowed_communities,
            },
        }


class ConfirmCommunityMigrationRequestType(NonDuplicableOARepoRecordRequestType):
    """Performs the primary community migration.

    The recipient of this request type should be the community owner of the new community.
    """

    type_id = "confirm_community_migration"
    name = _("confirm Community migration")

    payload_schema: Mapping[str, ma.fields.Field] | None = {
        "community": ma.fields.String(),
    }

    @classproperty[dict[str, type[RequestAction]]]
    @override
    def available_actions(  # type: ignore[override] # TODO: fix in requests
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": ConfirmCommunityMigrationAcceptAction,
        }

    @property
    def form(self) -> dict[str, Any]:
        """Form configuration."""
        return {
            "field": "community",
            "ui_widget": "TargetCommunitySelector",
            "read_only_ui_widget": "SelectedTargetCommunity",
            "props": {
                "readOnlyLabel": _("Target community:"),
            },
        }

    @override
    @no_request_message(_("Confirm record community migration"))
    @on_request_submitted(_("Record community migration confirmation pending"))
    def stateful_name(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
        return _("Confirm record community migration")

    @override
    @no_request_message(
        _(
            "Confirm the migration of the record to the new primary community. "
            "This request must be accepted by responsible person(s) of the new community."
        )
    )
    @on_request_submitted_creator(
        _(
            "The confirmation request has been submitted to the target community. "
            "You will be notified about their decision by email."
        )
    )
    @on_request_submitted_receiver(
        _(
            "A request to confirm record community migration has been received. "
            "You can now accept or decline the request."
        )
    )
    @on_request_submitted(_("Record community migration confirmation request is pending."))
    @on_request_creator(_("Submit to confirm record community migration."))
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
