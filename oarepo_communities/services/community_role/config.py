from invenio_records_resources.services.base.config import ServiceConfig

from oarepo_communities.services.community_role.results import (
    CommunityRoleRecordItem,
    CommunityRoleRecordList,
)
from oarepo_communities.services.community_role.schema import CommunityRoleSchema


class CommunityRoleServiceConfig(ServiceConfig):
    service_id = "community-role"
    links_item = {}

    result_item_cls = CommunityRoleRecordItem
    result_list_cls = CommunityRoleRecordList
    schema = CommunityRoleSchema
