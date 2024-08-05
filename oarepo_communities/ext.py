from functools import cached_property

from .resources.community_records.config import CommunityRecordsResourceConfig
from .resources.community_records.resource import CommunityRecordsResource
from .resources.oarepo.config import OARepoCommunityConfig
from .resources.oarepo.resource import OARepoCommunityResource
from .services.community_records.config import CommunityRecordsServiceConfig
from .services.community_records.service import CommunityRecordsService
from .services.oarepo.config import OARepoCommunityServiceConfig
from .services.oarepo.service import OARepoCommunityService
from .utils import get_urlprefix_service_id_mapping
from .workflow import community_default_workflow


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
        app.extensions["oarepo-communities"] = self

    def init_config(self, app):
        """Initialize configuration."""

        from . import config, ext_config

        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(
            config.REQUESTS_ALLOWED_RECEIVERS
        )
        app.config.setdefault("ENTITY_REFERENCE_UI_RESOLVERS", {}).update(
            config.ENTITY_REFERENCE_UI_RESOLVERS
        )
        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

    @cached_property
    def urlprefix_serviceid_mapping(self):
        return get_urlprefix_service_id_mapping()

    def get_community_default_workflow(self, **kwargs):
        return community_default_workflow(**kwargs)

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
        self.oarepo_community_service = OARepoCommunityService(
            OARepoCommunityServiceConfig()
        )

    def init_resources(self, app):
        """Initialize communities resources."""
        # Resources
        self.community_records_resource = CommunityRecordsResource(
            config=CommunityRecordsResourceConfig.build(app),
            service=self.community_records_service,
        )
        self.oarepo_community_resource = OARepoCommunityResource(
            config=OARepoCommunityConfig(),
            service=self.oarepo_community_service,
        )
