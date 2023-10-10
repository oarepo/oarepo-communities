import marshmallow as ma
from invenio_communities.communities.resources import CommunityResourceConfig
from invenio_communities.communities.resources.config import community_error_handlers

from invenio_records_resources.services.base.config import ConfiguratorMixin


class RecordCommunitiesResourceConfig(CommunityResourceConfig, ConfiguratorMixin):
    """Record communities resource config."""

    #blueprint_name = "records-community"
    #url_prefix = "/nr-documents/"
    routes = {
        "list": "/<pid_value>/communities",
        "suggestions": "/<pid_value>/communities-suggestions",
        "draft-list": "/<pid_value>/draft/communities",
    }

    request_extra_args = {
        "expand": ma.fields.Boolean(),
        "membership": ma.fields.Boolean(),
    }

    error_handlers = community_error_handlers