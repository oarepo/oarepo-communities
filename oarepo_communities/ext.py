from functools import cached_property

from .resources.community_records.config import CommunityRecordsResourceConfig
from .resources.community_records.resource import CommunityRecordsResource
from .services.community_records.config import CommunityRecordsServiceConfig
from .services.community_records.service import CommunityRecordsService
from .utils import get_urlprefix_service_id_mapping


class OARepoCommunities(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        self.init_services(app)
        self.init_resources(app)
        self.init_config(app)
        self.init_registry(app)
        app.extensions["oarepo-communities"] = self

    def init_config(self, app):
        """Initialize configuration."""

        from . import config

        app.config.setdefault("REQUESTS_REGISTERED_TYPES", []).extend(
            config.REQUESTS_REGISTERED_TYPES
        )
        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(
            config.REQUESTS_ALLOWED_RECEIVERS
        )
        app.config.setdefault("REQUESTS_ENTITY_RESOLVERS", []).extend(
            config.REQUESTS_ENTITY_RESOLVERS
        )
        app.config.setdefault("ENTITY_REFERENCE_UI_RESOLVERS", {}).update(
            config.ENTITY_REFERENCE_UI_RESOLVERS
        )

    @cached_property
    def urlprefix_serviceid_mapping(self):
        return get_urlprefix_service_id_mapping()

    @property
    def record_workflow(self):
        return self.app.config["RECORD_WORKFLOWS"]

    @property
    def community_records_services(self):
        return self.app.config["COMMUNITY_RECORDS_SERVICES"]

    def init_services(self, app):
        """Initialize communities service."""
        # Services
        self.community_records_service = CommunityRecordsService(
            config=CommunityRecordsServiceConfig.build(app),
        )

    def init_resources(self, app):
        """Initialize communities resources."""
        # Resources
        self.community_records_resource = CommunityRecordsResource(
            config=CommunityRecordsResourceConfig.build(app),
            service=self.community_records_service,
        )

    def init_registry(self, app):
        # resolvers aren't registered if they are intiated after invenio-requests
        # the same problem could happen for all stuff that needs to be registered?
        # ? perhaps we should have one method somewhere for registering everything after the ext init phase
        if "invenio-requests" in app.extensions:
            requests = app.extensions["invenio-requests"]
            resolvers = app.config.get("REQUESTS_ENTITY_RESOLVERS", [])
            registry = requests.entity_resolvers_registry
            for resolver in resolvers:
                registry.register_type(resolver, force=False)
