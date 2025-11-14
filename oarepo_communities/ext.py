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

from typing import TYPE_CHECKING, Any

from flask_principal import identity_loaded

import oarepo_communities.cli
import oarepo_communities.config

from .resolvers.communities import CommunityRoleResolver
from .services.community_role.config import CommunityRoleServiceConfig
from .services.community_role.service import CommunityRoleService
from .utils import load_community_user_needs
from .workflow import community_default_workflow

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

        app.config.setdefault("NOTIFICATION_RECIPIENTS_RESOLVERS", {})
        """
        app.config["NOTIFICATION_RECIPIENTS_RESOLVERS"] = conservative_merger.merge(
            app_registered_event_types, config.NOTIFICATION_RECIPIENTS_RESOLVERS
        )
        """

        app.config.setdefault(
            "OAREPO_COMMUNITIES_DEFAULT_WORKFLOW",
            oarepo_communities.config.OAREPO_COMMUNITIES_DEFAULT_WORKFLOW,
        )

        app.config.setdefault(
            "COMMUNITIES_RECORDS_SEARCH_ALL",
            config.COMMUNITIES_RECORDS_SEARCH_ALL,
        )

    def get_community_default_workflow(self, **kwargs: Any) -> Workflow:
        """Get default workflow for the community.

        It will have a look if the kwargs contain 'community_metadata' or 'record' or 'data'
        and will try to get the community from there. If no community is found, it will
        raise an exception.
        """
        return community_default_workflow(**kwargs)

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
