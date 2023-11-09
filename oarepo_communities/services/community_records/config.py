from invenio_communities.communities.records.api import Community
from invenio_records_resources.services.base.config import ConfiguratorMixin
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.links import pagination_links
from oarepo_runtime.config.service import PermissionsPresetsConfigMixin

from .schema import CommunityRecordsSchema

# from .schemas import RDMParentSchema, RDMRecordSchema
# from .schemas.community_records import CommunityRecordsSchema


class CommunityRecordsServiceConfig(
    PermissionsPresetsConfigMixin, RecordServiceConfig, ConfiguratorMixin
):
    """Community records service config."""

    # define at builder level: record_cls
    # schema = RDMRecordSchema
    # record service
    record_communities_service = None

    service_id = "community-records"
    community_cls = Community
    # permission_policy_cls = FromConfig(
    #    "RDM_PERMISSION_POLICY", default=RDMRecordPermissionPolicy, import_string=True
    # ) #how to use these things?

    # Search configuration
    # search = FromConfigSearchOptions(
    #    "RDM_SEARCH",
    #    "RDM_SORT_OPTIONS",
    #    "RDM_FACETS",
    #    search_option_cls=RDMSearchOptions,
    # )
    # search_versions = FromConfigSearchOptions(
    #    "RDM_SEARCH_VERSIONING",
    #    "RDM_SORT_OPTIONS",
    #    "RDM_FACETS",
    #    search_option_cls=RDMSearchVersionsOptions,
    # )

    # Service schemas
    community_record_schema = CommunityRecordsSchema

    # Max n. records that can be removed at once
    max_number_of_removals = 10

    links_search_community_records = pagination_links(
        "{+api}/communities/{id}/records{?args*}"
    )
