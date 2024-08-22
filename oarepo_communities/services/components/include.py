from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_communities.errors import MissingDefaultCommunityError
from oarepo_communities.proxies import current_oarepo_communities
from ..permissions.generators import convert_community_ids_to_uuid


class CommunityInclusionComponent(ServiceComponent):

    def create(self, identity, data=None, record=None, **kwargs):
        try:
            community_id = data["parent"]["communities"]["default"]
        except KeyError:
            raise MissingDefaultCommunityError(
                "Default community not defined in input."
            )

        current_oarepo_communities.community_inclusion_service.include(
            record,
            convert_community_ids_to_uuid(community_id),
            record_service=self.service,
            uow=self.uow,
        )
