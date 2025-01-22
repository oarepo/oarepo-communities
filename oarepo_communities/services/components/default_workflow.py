from __future__ import annotations
from typing import TYPE_CHECKING

from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any
    from flask_principal import Identity


class CommunityDefaultWorkflowComponent(ServiceComponent):

    def create(
        self, identity: Identity, data: dict[str, Any] = None, **kwargs: Any
    ) -> None:
        try:
            data["parent"]["workflow"]
        except KeyError:
            workflow_id = current_oarepo_communities.get_community_default_workflow(
                data=data
            )
            data.setdefault("parent", {})["workflow"] = workflow_id
