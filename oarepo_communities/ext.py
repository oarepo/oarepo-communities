from functools import cached_property

from .resources.community_records.config import CommunityRecordsResourceConfig
from .resources.community_records.resource import CommunityRecordsResource
from .services.community_records.config import CommunityRecordsServiceConfig
from .services.community_records.service import CommunityRecordsService
from .utils.utils import get_urlprefix_service_id_mapping


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
        app.extensions["oarepo-communities"] = self

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
