from __future__ import annotations

from typing import TYPE_CHECKING
from oarepo_runtime.services.results import ResultsComponent
from invenio_communities.communities.records.api import Community
from oarepo_communities.utils import community_to_dict

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.records.api import Record


class RecordCommunitiesComponent(ResultsComponent):
    """Component for expanding communities on a record."""

    def update_data(
        self, identity: Identity, record: Record, projection: dict, expand: bool
    ) -> None:
        """Expand communities if requested."""
        if not expand:
            return

        record_communities = []
        for community_id in record.parent.communities.ids or []:
            try:
                community = Community.get_record(community_id)
                record_communities.append(community_to_dict(community))
            except Exception:
                continue

        default_community_id = (
            str(record.parent.communities.default.id)
            if record.parent.communities.default
            else None
        )

        # Sorting communities so the one with the default id is first
        record_communities.sort(
            key=lambda community: community["id"] != default_community_id
        )

        if record_communities:
            projection["expanded"]["communities"] = record_communities
