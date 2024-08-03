from invenio_records_resources.services.records.config import RecordServiceConfig
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin


class OARepoCommunityServiceConfig(PermissionsPresetsConfigMixin, RecordServiceConfig):
    """Community records service config."""

    PERMISSIONS_PRESETS = ["workflow-oarepo-community"]
    service_id = "oarepo-community"
