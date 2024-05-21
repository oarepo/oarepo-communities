from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    ServiceConfig,
)
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin


class RecordCommunitiesServiceConfig(
    PermissionsPresetsConfigMixin, ServiceConfig, ConfiguratorMixin
):
    """Record communities service config."""
