#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component for setting workflow in the review process."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_drafts_resources.records import Record


class SetWorkflowInReviewComponent(ServiceComponent):
    """Component handling the workflow setup for a record in the review process."""

    def create_review(
        self,
        identity: Identity,  # noqa: ARG002
        data: dict[str, Any],
        record: Record,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Set workflow for the record in the review process if it is not set yet."""
        if record.parent.workflow is not None:
            return
        community_id = (
            data["receiver"]["community_role"].split(":")[0]
            if "community_role" in data["receiver"]
            else data["receiver"]["community"]
        )
        workflow = current_oarepo_communities.get_community_default_workflow(community_id=community_id)
        record.parent.workflow = workflow.code
