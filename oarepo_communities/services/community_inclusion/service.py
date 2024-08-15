from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.uow import RecordIndexOp, unit_of_work

from oarepo_communities.errors import CommunityNotIncludedException


class CommunityInclusionService(Service):
    """Record communities service.

    The communities service is in charge of managing communities of a given record.
    """

    def __init__(self):
        super().__init__(None)

    @unit_of_work()
    def include(self, record, community_id, record_service, uow=None, default=None):
        if default is None:
            default = not record.parent.communities
        record.parent.communities.add(community_id, default=default)

        uow.register(
            ParentRecordCommitOp(
                record.parent, indexer_context=dict(service=record_service)
            )
        )
        # comment from RDM:
        # this indexed record might not be the latest version: in this case, it might
        # not be immediately visible in the community's records, when the `all versions`
        # facet is not toggled
        # todo how to synchronize with rdm sources
        uow.register(
            RecordIndexOp(record, indexer=record_service.indexer, index_refresh=True)
        )
        """
        uow.register(
            NotificationOp(
                CommunityInclusionAcceptNotificationBuilder.build(
                    identity=identity, request=self.request
                )
            )
        )
        """
        return record

    @unit_of_work()
    def remove(self, record, community_id, record_service, uow=None):
        """Remove a community from the record."""

        # Default community is deleted when the exact same community is removed from the record
        if community_id not in record.parent.communities.ids:
            raise CommunityNotIncludedException
        record.parent.communities.remove(str(community_id))
        uow.register(
            ParentRecordCommitOp(
                record.parent,
                indexer_context=dict(service=record_service),
            )
        )
        uow.register(
            RecordIndexOp(record, indexer=record_service.indexer, index_refresh=True)
        )

    # todo links to communities on record (through record service config)
