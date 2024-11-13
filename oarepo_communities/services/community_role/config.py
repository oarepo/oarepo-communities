from invenio_records_resources.services.base.config import ServiceConfig
from oarepo_runtime.services.results import ArrayRecordItem, ArrayRecordList

from oarepo_communities.services.community_role.schema import CommunityRoleSchema


class CommunityRoleServiceConfig(ServiceConfig):
    service_id = "community-role"
    links_item = {}

    result_item_cls = ArrayRecordItem
    result_list_cls = ArrayRecordList
    schema = CommunityRoleSchema
