from __future__ import annotations
import marshmallow as ma
from invenio_access.permissions import system_identity
from invenio_requests.proxies import current_requests_service
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.proxies import current_oarepo_requests_service
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _
from oarepo_requests.utils import (
    classproperty,
    is_auto_approved,
    request_identity_matches,
    open_request_exists,
)
from oarepo_ui.resources.components import AllowedCommunitiesComponent


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
    from invenio_requests.customizations.actions import RequestAction
    from invenio_requests.records.api import Request

    from oarepo_requests.typing import EntityReference


class InitiateCommunityMigrationAcceptAction(OARepoAcceptAction):
    """
    Source community accepting the initiate request autocreates confirm request delegated to the target community.
    """

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        creator_ref = ResolverRegistry.reference_identity(identity)
        request_item = current_oarepo_requests_service.create(
            system_identity,
            data={"payload": self.request.get("payload", {})},
            request_type=ConfirmCommunityMigrationRequestType.type_id,
            topic=topic,
            creator=creator_ref,
            uow=uow,
            *args,
            **kwargs,
        )
        current_requests_service.execute_action(
            system_identity, request_item.id, "submit", uow=uow
        )


class ConfirmCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        community_id, role = (
            self.request.receiver.resolve().entities[0]._parse_ref_dict()
        )

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

    description = _("Request initiation of Community migration.")

    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
    payload_schema = {
        "community": ma.fields.String(required=True),
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
        if is_auto_approved(self, identity=identity, topic=topic):
            return _("Inititiate Community migration")
        if not request:
            return _("Request community migration")
        match request.status:
            case "submitted":
                return _("Community migration initiated")
            case _:
                return _("Request community migration")

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
                "Click to immediately start migration. "
                "After submitting the request will immediatelly be forwarded to responsible person(s) in the target community."
            )

        if not request:
            return _(
                "After you submit community migration request, it will first have to be approved by curators/owners of the current community. "
                "Then it will have to be accepted by curators/owners of the target community. "
                "You will be notified about the decision by email."
            )
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "The community migration request has been submitted. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "User has requested community migration. "
                        "You can now accept or decline the request."
                    )
                return _("Community migration request has been submitted.")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to initiate community migration. ")

                return _("Request not yet submitted.")

    form = {
        "field": "community",
        "ui_widget": "TargetCommunitySelector",
        "read_only_ui_widget": "SelectedTargetCommunity",
        "props": {
            "requestType": "initiate_community_migration",
        },
    }

    editable = False

    @classmethod
    @property
    def available_actions(cls):
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
            topic, "confirm_community_migration"
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

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
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

    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    form = {
        "field": "community",
        "read_only_ui_widget": "SelectedTargetCommunity",
        "props": {
            "requestType": "initiate_community_migration",
            "placeholder": _("Yes or no"),
            "community": {"id": "community", "label": _("Community")},
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
        # if is_auto_approved(self, identity=identity, topic=topic):
        #     return _("Migrate record")

        if not request:
            return _("Confirm community migration")
        match request.status:
            case "submitted":
                return _("Community migration confirmation pending")
            case _:
                return _("Confirm community migration")

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
        # if is_auto_approved(self, identity=identity, topic=topic):
        #     return _(
        #         "Click to immediately migrate record to a different community. "
        #         "After submitting the record will immediatelly be migrated to another community."
        #     )

        if not request:
            return _(
                "Confirm the migration of the record to the new primary community. "
                "This request must be accepted by the curators/owners of the new community."
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
                        "A request to confirm the community migration has been received. "
                        "You can now accept or decline the request."
                    )
                return _("The community migration confirmation request is pending.")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit to confirm the community migration.")
                return _("Request not yet submitted.")

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": ConfirmCommunityMigrationAcceptAction,
        }
