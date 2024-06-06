from invenio_drafts_resources.services import RecordService as InvenioRecordService
from invenio_records_resources.services.uow import unit_of_work

from oarepo_communities.utils.utils import get_associated_service


class RecordService(InvenioRecordService):
    def check_permission(self, identity, action_name, **kwargs):
        if action_name == "create":
            # required permission create_in_community has already been called
            return True
        return super().check_permission(identity, action_name, **kwargs)

    @unit_of_work()
    def create(
        self, identity, data, *args, community, uow=None, expand=False, **kwargs
    ):
        # todo can create - members of community
        self.require_permission(identity, "create_in_community", community=community)
        result_item = super().create(identity, data, uow=uow, expand=expand)
        record_communities_service = get_associated_service(self, "record_communities")

        record_communities_service.include(
            result_item._record,
            community.id,
            record_service=self,
            uow=uow,
        )
        return result_item
