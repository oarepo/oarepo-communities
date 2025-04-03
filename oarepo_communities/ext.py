from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from deepmerge import conservative_merger
from flask_principal import identity_loaded

import oarepo_communities.cli  # noqa - imported to register CLI commands

from .resources.community_records.config import CommunityRecordsResourceConfig
from .resources.community_records.resource import CommunityRecordsResource
from .services.community_inclusion.service import CommunityInclusionService
from .services.community_records.config import CommunityRecordsServiceConfig
from .services.community_records.service import CommunityRecordsService
from .services.community_role.config import CommunityRoleServiceConfig
from .services.community_role.service import CommunityRoleService
from .utils import get_urlprefix_service_id_mapping, load_community_user_needs
from .workflow import community_default_workflow

if TYPE_CHECKING:
    from flask import Flask


class OARepoCommunities(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app: Flask = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        self.init_services(app)
        self.init_resources(app)
        self.init_hooks(app)
        self.init_config(app)
        app.extensions["oarepo-communities"] = self

    def init_config(self, app: Flask) -> None:
        """Initialize configuration."""

        from . import config, ext_config

        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(
            config.REQUESTS_ALLOWED_RECEIVERS
        )
        app.config.setdefault(
            "OAREPO_REQUESTS_DEFAULT_RECEIVER", config.OAREPO_REQUESTS_DEFAULT_RECEIVER
        )
        app.config.setdefault("DEFAULT_COMMUNITIES_CUSTOM_FIELDS", []).extend(
            config.DEFAULT_COMMUNITIES_CUSTOM_FIELDS
        )
        app.config.setdefault("DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI", []).extend(
            config.DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI
        )
        app.config.setdefault("ENTITY_REFERENCE_UI_RESOLVERS", {}).update(
            config.ENTITY_REFERENCE_UI_RESOLVERS
        )
        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}
        app.config.setdefault(
            "DISPLAY_USER_COMMUNITIES", config.DISPLAY_USER_COMMUNITIES
        )
        app.config.setdefault("DISPLAY_NEW_COMMUNITIES", config.DISPLAY_NEW_COMMUNITIES)

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

        app.config["COMMUNITIES_ROUTES"] = {
            **config.COMMUNITIES_ROUTES,
            **app.config.get("COMMUNITIES_ROUTES", {}),
        }

        app_registered_event_types = app.config.setdefault(
            "NOTIFICATION_RECIPIENTS_RESOLVERS", {}
        )
        app.config["NOTIFICATION_RECIPIENTS_RESOLVERS"] = conservative_merger.merge(
            app_registered_event_types, config.NOTIFICATION_RECIPIENTS_RESOLVERS
        )
        app.config.setdefault("DATASTREAMS_TRANSFORMERS", {}).update(
            config.DATASTREAMS_TRANSFORMERS
        )

    @cached_property
    def urlprefix_serviceid_mapping(self) -> dict[str, str]:
        return get_urlprefix_service_id_mapping()

    def get_community_default_workflow(self, **kwargs) -> str | None:
        return community_default_workflow(**kwargs)

    def init_services(self, app: Flask) -> None:
        """Initialize communities service."""
        # Services
        self.community_records_service = CommunityRecordsService(
            config=CommunityRecordsServiceConfig.build(app),
        )

        self.community_inclusion_service = CommunityInclusionService()
        self.community_role_service = CommunityRoleService(
            config=CommunityRoleServiceConfig()
        )

    def init_resources(self, app: Flask) -> None:
        """Initialize communities resources."""
        # Resources
        self.community_records_resource = CommunityRecordsResource(
            config=CommunityRecordsResourceConfig.build(app),
            service=self.community_records_service,
        )

    def init_hooks(self, app: Flask) -> None:
        """Initialize hooks."""

        @identity_loaded.connect_via(app)
        def on_identity_loaded(_, identity):
            load_community_user_needs(identity)

    """
    def get_default_community_from_record(self, record: Record, **kwargs: Any):
        record = record.parent if hasattr(record, "parent") else record
        try:
            return record.communities.default.id
        except AttributeError:
            return None
    """


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""

    # Register services - cannot be done in extension because
    # Invenio-Records-Resources might not have been initialized.
    rr_ext = app.extensions["invenio-records-resources"]
    # idx_ext = app.extensions["invenio-indexer"]
    ext = app.extensions["oarepo-communities"]

    # services
    rr_ext.registry.register(
        ext.community_records_service,
        service_id=ext.community_records_service.config.service_id,
    )
    rr_ext.registry.register(
        ext.community_role_service,
        service_id=ext.community_role_service.config.service_id,
    )
    # indexers
    # idx_ext.registry.register(ext.community_records_service.indexer, indexer_id="communities")

    #
    # Workaround for https://github.com/inveniosoftware/invenio-communities/pull/1192
    #
    if isinstance(app.config["COMMUNITIES_CUSTOM_FIELDS"], dict):
        assert not app.config["COMMUNITIES_CUSTOM_FIELDS"]
        app.config["COMMUNITIES_CUSTOM_FIELDS"] = []

    if isinstance(app.config["COMMUNITIES_CUSTOM_FIELDS_UI"], dict):
        assert not app.config["COMMUNITIES_CUSTOM_FIELDS_UI"]
        app.config["COMMUNITIES_CUSTOM_FIELDS_UI"] = []
    #
    # end of workaround
    #

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

    if not app.config.get("WORKFLOWS"):
        # set up default workflows if not set
        from .ext_config import COMMUNITY_WORKFLOWS

        app.config["WORKFLOWS"] = COMMUNITY_WORKFLOWS

    if not app.config.get("COMMUNITIES_ROLES"):
        # set up default roles if not set up
        from .ext_config import DEFAULT_COMMUNITIES_ROLES

        app.config["COMMUNITIES_ROLES"] = DEFAULT_COMMUNITIES_ROLES
