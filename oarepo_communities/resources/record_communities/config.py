from invenio_communities.communities.resources import CommunityResourceConfig
from invenio_communities.communities.resources.config import community_error_handlers
from invenio_records_resources.services.base.config import ConfiguratorMixin


class RecordCommunitiesResourceConfig(CommunityResourceConfig, ConfiguratorMixin):
    """Record communities resource config."""

    routes = {
        "list": "/<pid_value>/communities",
    }

    error_handlers = community_error_handlers
