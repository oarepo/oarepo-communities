from invenio_communities.proxies import current_communities
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_pidstore.errors import PIDUnregistered
from invenio_records_resources.services import RecordIndexerMixin
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.uow import RecordIndexOp, unit_of_work
from invenio_search.engine import dsl

from oarepo_communities.services.errors import RecordCommunityMissing
from oarepo_communities.utils import slug2id


class CommunityInclusionService(Service):
    """Record communities service.

    The communities service is in charge of managing communities of a given record.
    """

    @unit_of_work()
    def include(
        self, record, community_id, uow=None, record_service=None, default=None
    ):
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
            RecordIndexOp(
                record, indexer=record_service.indexer, index_refresh=True
            )
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
    def remove(self, record, community_id, record_service=None, uow=None):
        """Remove a community from the record."""
        # todo unslug somewhere else
        if community_id not in record.parent.communities.ids:
            # try if it's the community slug instead
            community_id = slug2id(community_id)
            if community_id not in record.parent.communities.ids:
                raise RecordCommunityMissing(record.id, community_id)

        # Default community is deleted when the exact same community is removed from the record
        record.parent.communities.remove(community_id)
        uow.register(
            ParentRecordCommitOp(
                record.parent,
                indexer_context=dict(service=record_service),
            )
        )
        uow.register(
            RecordIndexOp(
                record, indexer=record_service.indexer, index_refresh=True
            )
        )

    # todo links to communities on record (through record service config)