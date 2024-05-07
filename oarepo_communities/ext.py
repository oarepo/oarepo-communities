from .cache import aai_mapping, permissions_cache
from .resources.community_records.config import CommunityRecordsResourceConfig
from .resources.community_records.resource import CommunityRecordsResource
from .services.community_records.config import CommunityRecordsServiceConfig
from .services.community_records.service import CommunityRecordsService


class OARepoCommunities(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_services(app)
        self.init_resources(app)
        app.extensions["oarepo-communities"] = self

    def init_config(self, app):
        """Initialize configuration."""
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][
                    k
                ] = ext_config.OAREPO_PERMISSIONS_PRESETS[k]

        self.permissions_cache = permissions_cache
        self.aai_mapping = aai_mapping

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