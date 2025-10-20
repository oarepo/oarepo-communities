#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component setting default workflow from a community when a record is created."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from oarepo_workflows.services.components.workflow import WorkflowSetupComponent

from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity


class CommunityDefaultWorkflowComponent(WorkflowSetupComponent):
    """Component setting default workflow from a community when a record is created."""

    # affects all components, so should be placed as the first one
    affects = "*"

    @override
    def create(self, identity: Identity, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if data is None:
            raise ValueError("data is required when creating a record")  # pragma: no cover

        if not data.get("parent", {}).get("workflow"):
            workflow = current_oarepo_communities.get_community_default_workflow(data=data)
            data.setdefault("parent", {})["workflow"] = workflow.code
