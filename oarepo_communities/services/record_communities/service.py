from invenio_communities.proxies import current_communities
from invenio_drafts_resources.services import RecordService

# from invenio_i18n import lazy_gettext as _
# from invenio_notifications.services.uow import NotificationOp
from invenio_pidstore.errors import PIDUnregistered
from invenio_records_resources.services import RecordIndexerMixin, ServiceSchemaWrapper
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordIndexOp,
    unit_of_work,
)
from invenio_search.engine import dsl

from oarepo_communities.services.errors import RecordCommunityMissing
from oarepo_communities.utils.utils import slug2id


class RecordCommunitiesService(RecordService, RecordIndexerMixin):
    """Record communities service.

    The communities service is in charge of managing communities of a given record.
    """

    def __init__(self, config, record_service=None):
        super().__init__(config)
        self.record_service = record_service

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @property
    def record_cls(self):
        """Factory for creating a record class."""
        return self.config.record_cls

    def _resolve_record(self, id_):
        try:
            return self.record_cls.pid.resolve(id_)
        except PIDUnregistered:
            return self.draft_cls.pid.resolve(id_, registered_only=False)

    @unit_of_work()
    def include(
        self, record, community_id, uow=None, record_service=None, default=None
    ):
        applied_record_service = record_service or self.record_service

        if default is None:
            default = not record.parent.communities
        record.parent.communities.add(community_id, default=default)
        uow.register(RecordCommitOp(record.parent))
        uow.register(
            RecordIndexOp(
                record, indexer=applied_record_service.indexer, index_refresh=True
            )
        )
        return record

    @unit_of_work()
    def remove(self, record, community_id, record_service=None, uow=None):
        """Remove a community from the record."""
        applied_record_service = record_service or self.record_service
        if community_id not in record.parent.communities.ids:
            # try if it's the community slug instead
            community_id = slug2id(community_id)
            if community_id not in record.parent.communities.ids:
                raise RecordCommunityMissing(record.id, community_id)

        # Default community is deleted when the exact same community is removed from the record
        record.parent.communities.remove(community_id)
        uow.register(RecordCommitOp(record.parent))
        uow.register(RecordIndexOp(record, indexer=applied_record_service.indexer))

    def search(
        self,
        identity,
        id_,
        params=None,
        search_preference=None,
        expand=False,
        extra_filter=None,
        **kwargs,
    ):
        """Search for record's communities."""
        record = self._resolve_record(id_)
        self.require_permission(identity, "read", record=record)

        communities_ids = record.parent.communities.ids
        communities_filter = dsl.Q("terms", **{"id": [id_ for id_ in communities_ids]})
        if extra_filter is not None:
            communities_filter = communities_filter & extra_filter

        return current_communities.service.search(
            identity,
            params=params,
            search_preference=search_preference,
            expand=expand,
            extra_filter=communities_filter,
            **kwargs,
        )
