from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    ServiceConfig,
)
from invenio_records_resources.services.records.links import pagination_links
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin


class CommunityRecordsServiceConfig(
    PermissionsPresetsConfigMixin, ServiceConfig, ConfiguratorMixin
):
    """Community records service config."""

    PERMISSIONS_PRESETS = ["workflow"]
    service_id = "community-records"
    links_search_community_records = pagination_links(
        "{+api}/communities/{id}/records{?args*}"
    )
    links_search_community_user_records = pagination_links(
        "{+api}/communities/{id}/user/records{?args*}"
    )
    links_search_community_model_records = pagination_links(
        "{+api}/communities/{id}/{model}{?args*}"
    )
    links_search_community_model_user_records = pagination_links(
        "{+api}/communities/{id}/user/{model}{?args*}"
    )
