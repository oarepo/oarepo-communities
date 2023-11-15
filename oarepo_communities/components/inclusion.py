import functools

from invenio_access.permissions import system_identity
from invenio_records_resources.services.records.components import ServiceComponent
from oarepo_communities.services.record_communities.service import include_record_in_community
from invenio_communities.proxies import current_communities

class SetCommunityComponent(ServiceComponent):
    """
    def __init__(self, record_communities_service, *args, **kwargs):
        self.record_communities_service = record_communities_service
        super().__init__(*args, **kwargs)
    """

    def create(self, identity, data=None, record=None, **kwargs):
        if "community_id" not in data:
            #todo log
            return
        community_id = data["community_id"]
        include_record_in_community(record, community_id, self.service, self.uow)
        """
        self.service.config.record_communities_service.add_to_record(
            system_identity,
            record,
            {"communities": [{"id": community_id}]},
            uow=self.uow,
        )
        """

"""
def SetCommunityComponent(record_communities_service):
    return functools.partial(SetCommunityComponentPrivate, record_communities_service)
"""
