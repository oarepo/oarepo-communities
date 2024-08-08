from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    ServiceConfig,
)


class CommunityInclusionServiceConfig(ServiceConfig, ConfiguratorMixin):
    """Record communities service config."""

    components = []
