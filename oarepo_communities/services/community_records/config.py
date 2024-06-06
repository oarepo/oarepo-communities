from invenio_records_resources.services.base.config import ConfiguratorMixin
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.links import pagination_links
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin

from .schema import CommunityRecordsSchema


class CommunityRecordsServiceConfig(
    PermissionsPresetsConfigMixin, RecordServiceConfig, ConfiguratorMixin
):
    """Community records service config."""

    PERMISSIONS_PRESETS = ["community"]
    service_id = "community-records"
    community_record_schema = CommunityRecordsSchema
    # todo correct links
    links_search_community_records = pagination_links(
        "{+api}/communities/{id}/records{?args*}"
    )
