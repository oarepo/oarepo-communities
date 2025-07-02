from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_communities.errors import MissingDefaultCommunityError
from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_drafts_resources.records import Record


class CommunityInclusionComponent(ServiceComponent):

    def create(
        self,
        identity: Identity,
        data: dict[str, Any] = None,
        record: Record = None,
        **kwargs: Any,
    ) -> None:
        try:
            community_id = data["parent"]["communities"]["default"].id
        except KeyError:
            raise MissingDefaultCommunityError(
                "Default community not defined in input."
            )

        current_oarepo_communities.community_inclusion_service.include(
            record,
            community_id,
            record_service=self.service,
            uow=self.uow,
        )
