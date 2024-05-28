from invenio_access.permissions import system_identity
from invenio_drafts_resources.services import RecordService as InvenioRecordService
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.uow import unit_of_work


class RecordService(InvenioRecordService):

    @unit_of_work()
    def create(self, identity, data, uow=None, expand=False, *args, **kwargs):
        if "community" not in kwargs:
            raise PermissionDeniedError(
                "Attempt to create record outside of community."
            )
        community = kwargs["community"]
        self.require_permission(identity, "create_in_community", community=community)
        return super().create(identity, data, uow=uow, expand=expand)

    @unit_of_work()
    def publish(self, identity, id_, uow=None, expand=False, *args, **kwargs):
        if identity != system_identity and (
            "is_request" not in kwargs or not kwargs["is_request"]
        ):
            raise PermissionDeniedError(
                "Publish is not done through request or system process."
            )
        return super().publish(identity, id_, uow=uow, expand=expand)

    @unit_of_work()
    def delete(self, identity, id_, revision_id=None, uow=None, *args, **kwargs):
        if identity != system_identity and "is_request" not in kwargs:
            raise PermissionDeniedError(
                "Delete is not done through request or system process."
            )
        return super().delete(identity, id_, revision_id=revision_id, uow=uow)
