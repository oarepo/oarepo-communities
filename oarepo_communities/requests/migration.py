from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from flask import g
from invenio_access.permissions import system_identity
from invenio_requests.proxies import current_requests_service
from oarepo_requests.actions.generic import OARepoAcceptAction, RequestActionState
from oarepo_requests.proxies import current_oarepo_requests_service
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_requests.utils import (
    is_auto_approved,
    open_request_exists,
    request_identity_matches,
)
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _
from oarepo_ui.resources.components import AllowedCommunitiesComponent
from typing_extensions import override

from ..errors import (
    CommunityAlreadyIncludedException,
    TargetCommunityNotProvidedException,
)
from ..proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_records_resources.services.uow import UnitOfWork
    from invenio_requests.customizations import RequestType
    from invenio_requests.customizations.actions import RequestAction
    from invenio_requests.records.api import Request
    from oarepo_requests.typing import EntityReference
from invenio_requests.resolvers.registry import ResolverRegistry


class InitiateCommunityMigrationAcceptAction(OARepoAcceptAction):
    """
    Source community accepting the initiate request autocreates confirm request delegated to the target community.
    """

    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        created_by = self.request.created_by.resolve()
        request_item = current_oarepo_requests_service.create(
            system_identity,
            data={"payload": self.request.get("payload", {})},
            request_type=ConfirmCommunityMigrationRequestType.type_id,
            topic=state.topic,
            creator=ResolverRegistry.reference_entity(created_by),
            uow=uow,
            *args,
            **kwargs,
        )
        current_requests_service.execute_action(
            system_identity, request_item.id, "submit", uow=uow
        )


class ConfirmCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        topic = state.topic
        community_id = self.request.get("payload", {}).get("community", None)
        if not community_id:
            raise TargetCommunityNotProvidedException("Target community not provided.")

        service = get_record_service_for_record(topic)
        community_inclusion_service = (
            current_oarepo_communities.community_inclusion_service
        )
        community_inclusion_service.remove(
            topic,
            str(topic.parent.communities.default.id),
            record_service=service,
            uow=uow,
        )
        community_inclusion_service.include(
            topic, community_id, record_service=service, uow=uow, default=True
        )


class InitiateCommunityMigrationRequestType(NonDuplicableOARepoRequestType):
    """Request which is used to start migrating record from one primary community to another one.
    The recipient of this request type should be the community role of the current primary community, that is the owner
    of the current community must agree that the record could be migrated elsewhere.
    When this request is accepted, a new request of type ConfirmCommunityMigrationRequestType should be created and
     submitted to perform the community migration.
    """

    type_id = "initiate_community_migration"
    name = _("Inititiate Community migration")

    description = _("Move record to another primary community.")

    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=False)
    payload_schema = {
        "community": ma.fields.String(),
    }
    receiver_can_be_none = True

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
        if is_auto_approved(self, identity=identity, topic=topic):
            return _("Inititiate record community migration")
        if not request:
            return _("Inititiate record community migration")
        match request.status:
            case "submitted":
                return _("Record community migration initiated")
            case _:
                return _("Request record community migration")

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
        if is_auto_approved(self, identity=identity, topic=topic):
            return _(
                "Click to immediately start record migration. "
                "After submitting the request will immediatelly be forwarded to responsible person(s) in the target community. "
                "You will be notified about the decision by email."
            )

        if not request:
            return _(
                "After you submit record community migration request, it will first have to be approved by responsible person(s) of the current community. "
                "Then it will have to be accepted by responsible persons(s) of the target community. "
                "You will be notified about the decision by email."
            )
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "Record community migration request has been submitted. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "User has requested record community migration. "
                        "You can now accept or decline the request."
                    )
                return _("Record community migration request has been submitted.")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to initiate record community migration. ")

                return _("Request not yet submitted.")

    @property
    def form(self):
        allowed_communities = AllowedCommunitiesComponent.get_allowed_communities(
            g.identity, "create"
        )
        allowed_communities = [
            AllowedCommunitiesComponent.community_to_dict(community)
            for community in allowed_communities
        ]
        return {
            "field": "community",
            "ui_widget": "TargetCommunitySelector",
            "read_only_ui_widget": "SelectedTargetCommunity",
            "props": {
                "readOnlyLabel": _("Target community:"),
                "allowedCommunities": allowed_communities,
            },
        }

    editable = False

    @classmethod
    @property
    def available_actions(cls) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": InitiateCommunityMigrationAcceptAction,
        }

    @classmethod
    def is_applicable_to(
        cls, identity: Identity, topic: Record, *args: Any, **kwargs: Any
    ) -> bool:
        """Check if the request type is applicable to the topic."""

        if open_request_exists(topic, cls.type_id) or open_request_exists(
            topic, ConfirmCommunityMigrationRequestType.type_id
        ):
            return False
        # check if the user has more than one community to which they can migrate
        allowed_communities_count = 0
        for _ in AllowedCommunitiesComponent.get_allowed_communities(
            identity, "create"
        ):
            allowed_communities_count += 1
            if allowed_communities_count > 1:
                break

        if allowed_communities_count <= 1:
            return False

        return super().is_applicable_to(identity, topic, *args, **kwargs)

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
        already_included = target_community_id == str(
            topic.parent.communities.default.id
        )
        if already_included:
            raise CommunityAlreadyIncludedException(
                "Already inside this primary community."
            )


class ConfirmCommunityMigrationRequestType(NonDuplicableOARepoRequestType):
    """
    Performs the primary community migration. The recipient of this request type should be the community
    owner of the new community.
    """

    type_id = "confirm_community_migration"
    name = _("confirm Community migration")

    allowed_topic_ref_types = ModelRefTypes(published=True, draft=False)

    payload_schema = {
        "community": ma.fields.String(),
    }

    @property
    def form(self):
        return {
            "field": "community",
            "ui_widget": "TargetCommunitySelector",
            "read_only_ui_widget": "SelectedTargetCommunity",
            "props": {
                "readOnlyLabel": _("Target community:"),
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
        if not request:
            return _("Confirm record community migration")
        match request.status:
            case "submitted":
                return _("Record community migration confirmation pending")
            case _:
                return _("Confirm record community migration")

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
                "Confirm the migration of the record to the new primary community. "
                "This request must be accepted by responsible person(s) of the new community."
            )

        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "The confirmation request has been submitted to the target community. "
                        "You will be notified about their decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "A request to confirm record community migration has been received. "
                        "You can now accept or decline the request."
                    )
                return _("Record community migration confirmation request is pending.")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to confirm record community migration.")
                return _("Request not yet submitted.")

    @classmethod
    @property
    def available_actions(cls) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": ConfirmCommunityMigrationAcceptAction,
        }
