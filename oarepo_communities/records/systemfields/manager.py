import uuid

from invenio_communities.records.records.systemfields.communities.manager import (
    CommunitiesRelationManager as InvenioCommunitiesRelationManager,
)
from invenio_records_resources.records import Record

from oarepo_communities.records.api import CommunityRoleRecord


class CommunitiesRelationManager(InvenioCommunitiesRelationManager):
    def _to_id(self, val: str | uuid.UUID | Record | CommunityRoleRecord) -> str | None:
        """Get the community id."""
        if isinstance(val, CommunityRoleRecord):
            return str(val.community.id)
        return super()._to_id(val)
