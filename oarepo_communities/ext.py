#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""oarepo-communities extension."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from deepmerge import conservative_merger
from flask_principal import identity_loaded
from invenio_communities.communities.records.api import Community
from invenio_pidstore.errors import PIDDoesNotExistError

import oarepo_communities.config

from .errors import CommunityDoesntExistError
from .resolvers.communities import CommunityRoleResolver
from .services.community_role.config import CommunityRoleServiceConfig
from .services.community_role.service import CommunityRoleService
from .utils import load_community_user_needs
from .workflow import get_workflow_from_community_custom_fields

if TYPE_CHECKING:
    from flask import Flask
    from flask_principal import Identity
    from oarepo_workflows import Workflow


class OARepoCommunities:
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app: Flask | None = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        self.init_services(app)
        self.init_hooks(app)
        self.init_config(app)
        app.extensions["oarepo-communities"] = self

    def init_config(self, app: Flask) -> None:
        """Initialize configuration."""
        from . import config

        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(config.REQUESTS_ALLOWED_RECEIVERS)
        app.config.setdefault("OAREPO_REQUESTS_DEFAULT_RECEIVER", config.OAREPO_REQUESTS_DEFAULT_RECEIVER)
        app.config.setdefault("DEFAULT_COMMUNITIES_CUSTOM_FIELDS", []).extend(config.DEFAULT_COMMUNITIES_CUSTOM_FIELDS)
        app.config.setdefault("DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI", []).extend(
            config.DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI
        )
        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}
        app.config.setdefault("DISPLAY_USER_COMMUNITIES", config.DISPLAY_USER_COMMUNITIES)
        app.config.setdefault("DISPLAY_NEW_COMMUNITIES", config.DISPLAY_NEW_COMMUNITIES)

        app.config["COMMUNITIES_ROUTES"] = {
            **config.COMMUNITIES_ROUTES,
            **app.config.get("COMMUNITIES_ROUTES", {}),
        }

        app_notification_recipients_resolvers = app.config.setdefault("NOTIFICATION_RECIPIENTS_RESOLVERS", {})
        app.config["NOTIFICATION_RECIPIENTS_RESOLVERS"] = conservative_merger.merge(
            app_notification_recipients_resolvers, config.NOTIFICATION_RECIPIENTS_RESOLVERS
        )

        app.config.setdefault(
            "OAREPO_COMMUNITIES_DEFAULT_WORKFLOW",
            oarepo_communities.config.OAREPO_COMMUNITIES_DEFAULT_WORKFLOW,
        )

        app.config.setdefault(
            "COMMUNITIES_RECORDS_SEARCH_ALL",
            config.COMMUNITIES_RECORDS_SEARCH_ALL,
        )

    def get_community_default_workflow(self, community_id: str) -> Workflow:
        """Get default workflow for the community.

        It will have a look if the kwargs contain 'community_metadata' or 'record' or 'data'
        and will try to get the community from there. If no community is found, it will
        raise an exception.
        """
        try:
            community = cast("Community", Community.pid.resolve(community_id))
        except PIDDoesNotExistError as e:
            raise CommunityDoesntExistError(community_id) from e

        return get_workflow_from_community_custom_fields(community.custom_fields)

    def init_services(self, _app: Flask) -> None:
        """Initialize communities service."""
        # Services
        self.community_role_service = CommunityRoleService(config=CommunityRoleServiceConfig())

    def init_hooks(self, app: Flask) -> None:
        """Initialize hooks."""

        @identity_loaded.connect_via(app)
        def on_identity_loaded(_: Flask, identity: Identity) -> None:
            load_community_user_needs(identity)


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    # Register services - cannot be done in extension because
    # Invenio-Records-Resources might not have been initialized.
    rr_ext = app.extensions["invenio-records-resources"]
    ext: OARepoCommunities = app.extensions["oarepo-communities"]

    # services
    rr_ext.registry.register(
        ext.community_role_service,
        service_id=ext.community_role_service.config.service_id,
    )

    for cf in app.config["DEFAULT_COMMUNITIES_CUSTOM_FIELDS"]:
        for target_cf in app.config["COMMUNITIES_CUSTOM_FIELDS"]:
            if cf.name == target_cf.name:
                break
        else:
            app.config["COMMUNITIES_CUSTOM_FIELDS"].append(cf)

    for cf in app.config["DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI"]:
        for target_cf in app.config["COMMUNITIES_CUSTOM_FIELDS_UI"]:
            if cf["section"] == target_cf["section"]:
                break
        else:
            app.config["COMMUNITIES_CUSTOM_FIELDS_UI"].append(cf)

    requests = app.extensions["invenio-requests"]
    requests.entity_resolvers_registry.register_type(CommunityRoleResolver())

    # replace SharedOrMyRequestsParam with CommunitiesSharedOrMyRequestsParam
    from invenio_requests.services.requests.config import SharedOrMyRequestsParam, UserRequestSearchOptions

    from oarepo_communities.services.params import CommunitiesSharedOrMyRequestsParam

    param_interpreter_classes = [
        param for param in UserRequestSearchOptions.params_interpreters_cls if param != SharedOrMyRequestsParam
    ]

    if not any(isinstance(param, CommunitiesSharedOrMyRequestsParam) for param in param_interpreter_classes):
        param_interpreter_classes.append(CommunitiesSharedOrMyRequestsParam)

    UserRequestSearchOptions.params_interpreters_cls = tuple(param_interpreter_classes)

    fix_hardcoded_roles(app)


def _replace_stock_roles(roles: list[str], replacements: dict[str, set[str]]) -> list[str]:
    """Return `roles` with stock role names substituted per `replacements`, deduplicated.

    Each role in `roles` that has an entry in `replacements` is expanded into the
    corresponding set of configured role names; any role without an entry is kept as-is.
    The result is a plain union of sets, so it is naturally deduplicated regardless of
    whether the duplicates were already present (e.g. "owner") or introduced by expanding
    two different stock names to overlapping configured roles.
    """
    result: set[str] = set()
    for role in roles:
        if role in replacements:
            result |= replacements[role]
        else:
            result.add(role)
    return sorted(result)


def _fix_recipient_roles(recipients: list | None, replacements: dict[str, set[str]]) -> None:
    """Recursively patch `CommunityMembersRecipient.roles` in a notification recipients list.

    Recipients can be nested inside conditional generators (e.g. `IfUserRecipient`'s
    `then_`/`else_` branches), so those are walked into as well.
    """
    from invenio_communities.notifications.generators import CommunityMembersRecipient
    from invenio_notifications.services.generators import ConditionalRecipientGenerator

    for recipient in recipients or []:
        if isinstance(recipient, CommunityMembersRecipient) and recipient.roles:
            recipient.roles = _replace_stock_roles(recipient.roles, replacements)
        elif isinstance(recipient, ConditionalRecipientGenerator):
            _fix_recipient_roles(recipient.then_, replacements)
            _fix_recipient_roles(recipient.else_, replacements)


def fix_hardcoded_roles(app: Flask) -> None:
    """Replace hardcoded community roles with configurable roles.

    Invenio in some places has hard-coded community role names. On the other hand, it provides
    a possibility to define custom roles that might be in conflict with the hard-coded ones.
    This patch replaces the hard-coded roles with the configurable ones.

    Concretely, several ``invenio_communities``/``invenio_rdm_records`` request types and
    notification builders hard-code the stock ``"manager"`` and ``"curator"`` role names (in
    ``needs_context["community_roles"]`` and in ``CommunityMembersRecipient(roles=[...])``)
    instead of reading the roles actually configured via ``COMMUNITIES_ROLES``. If a
    deployment does not define roles with those exact names (relying on differently-named
    roles for the manage-level / curate-level permission), members holding the differently
    named role are silently unable to act on / be notified about these requests.

    This function replaces ``"manager"``/``"curator"`` in those hard-coded role lists with
    the roles that are actually configured to have manage/curate permissions
    (``can_manage=True``/``can_curate=True`` in ``COMMUNITIES_ROLES``), keeping any other
    roles already listed (e.g. ``"owner"``, or anything Invenio might add there in the
    future) untouched.
    It is idempotent - it can be called repeatedly (e.g. once per app factory invocation)
    without accumulating changes.
    """
    from invenio_communities.members.services.request import (
        CommunityInvitation,
        MembershipRequestRequestType,
    )
    from invenio_communities.notifications import builders as community_notification_builders
    from invenio_communities.subcommunities.services.request import (
        SubCommunityInvitationRequest,
        SubCommunityRequest,
    )
    from invenio_rdm_records.notifications import builders as rdm_notification_builders
    from invenio_rdm_records.requests.community_inclusion import CommunityInclusion
    from invenio_rdm_records.requests.community_submission import CommunitySubmission

    communities_roles = app.config.get("COMMUNITIES_ROLES", [])
    manage_roles = {role["name"] for role in communities_roles if role.get("can_manage")}
    curate_roles = {role["name"] for role in communities_roles if role.get("can_curate")}

    replacements: dict[str, set[str]] = {}
    if manage_roles:
        replacements["manager"] = manage_roles
    if curate_roles:
        replacements["curator"] = curate_roles
    if not replacements:
        # roles are not configured (yet) - nothing to fix
        return

    # A. permission checks - requests that require the "manage"/"curate" community-level permission
    for request_type in (
        CommunityInvitation,
        MembershipRequestRequestType,
        SubCommunityRequest,
        SubCommunityInvitationRequest,
        CommunityInclusion,
        CommunitySubmission,
    ):
        # some invenio_communities/invenio_rdm_records request types are stubbed as
        # `needs_context: Optional[str]`/`Any`, even though it is always a dict at runtime
        needs_context = dict(cast("dict[str, object]", request_type.needs_context))
        community_roles = cast("list[str]", needs_context.get("community_roles", []))
        needs_context["community_roles"] = _replace_stock_roles(community_roles, replacements)
        request_type.needs_context = needs_context  # pyright: ignore[reportAttributeAccessIssue]

    # C. notification recipients - members that should be notified about the above requests
    for notification_builders in (community_notification_builders, rdm_notification_builders):
        for builder in vars(notification_builders).values():
            if isinstance(builder, type):
                _fix_recipient_roles(getattr(builder, "recipients", None), replacements)
