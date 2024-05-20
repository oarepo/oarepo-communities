from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_communities.utils.utils import get_associated_service


class CommunitiesComponent(ServiceComponent):
    def create(self, identity, *, record, **kwargs):
        data = kwargs["data"]
        try:
            community_id = data["parent"]["communities"]["default"]
        except KeyError:
            return

        record_communities_service = get_associated_service(
            self.service, "record_communities"
        )

        record_communities_service.include(
            record,
            community_id,
            record_service=self.service,
            uow=self.uow,
        )
