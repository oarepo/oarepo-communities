
from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_communities.services.record_communities.service import (
    include_record_in_community,
)

class SetCommunityComponent(ServiceComponent):
    def create(self, identity, data=None, record=None, **kwargs):
        if "community_id" not in data:
            # todo how to input this (from ui i suppose)?
            # todo log
            return
        community_id = data["community_id"]
        include_record_in_community(record, community_id, self.service, self.uow)


