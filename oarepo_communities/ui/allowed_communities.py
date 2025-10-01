#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI component that fills allowed communities for creating records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_communities.communities.records.api import Community
from invenio_i18n import gettext as _
from invenio_records_resources.services.errors import PermissionDeniedError
from oarepo_ui.resources.components.base import UIResourceComponent

from oarepo_communities.utils import community_to_dict

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_principal import Identity
    from invenio_records_resources.services.records.results import RecordItem
    from oarepo_workflows import Workflow


class AllowedCommunitiesComponent(UIResourceComponent):
    """UI component that fills allowed communities for creating records."""

    @override
    def form_config(
        self,
        *,
        api_record: RecordItem,
        record: dict,
        identity: Identity,
        form_config: dict,
        ui_links: dict,
        extra_context: dict,
        **kwargs: Any,
    ) -> None:
        sorted_allowed_communities = sorted(
            self.get_allowed_communities(identity, "create"),
            key=lambda community: community.metadata["title"],
        )

        form_config["allowed_communities"] = [community_to_dict(community) for community in sorted_allowed_communities]

    @override
    def before_ui_create(
        self,
        *,
        data: dict,
        identity: Identity,
        form_config: dict,
        ui_links: dict,
        extra_context: dict,
        community: str | None = None,
        **kwargs: Any,
    ) -> None:
        if community:
            try:
                preselected_community = next(
                    (c for c in form_config["allowed_communities"] if c["slug"] == community),
                )
            except StopIteration:
                raise PermissionDeniedError(_("You have no permission to create record in this community.")) from None
        else:
            preselected_community = None

        form_config["preselected_community"] = preselected_community

    @classmethod
    def get_allowed_communities(cls, identity: Identity, action: str) -> Generator[Community]:
        """Get communities where the user has the given permission."""
        community_ids = set()
        for need in identity.provides:
            if need.method == "community" and need.value:
                community_ids.add(need.value)

        for community_id in community_ids:
            community = Community.get_record(community_id)
            if cls.user_has_permission(identity, community, action):
                yield community

    @classmethod
    def user_has_permission(cls, identity: Identity, community: Community, action: str) -> bool:
        """Check if the user has permission to perform the action in the community."""
        workflow = community.custom_fields.get("workflow", "default")
        return cls.check_user_permissions(str(community.id), workflow, identity, action)

    @classmethod
    def check_user_permissions(cls, community_id: str, workflow_id: str, identity: Identity, action: str) -> bool:
        """Check if the user has permission to perform the action in the workflow."""
        from oarepo_workflows.errors import InvalidWorkflowError
        from oarepo_workflows.proxies import current_oarepo_workflows

        try:
            wf: Workflow = next(iter(x for x in current_oarepo_workflows.record_workflows if x.code == workflow_id))
        except StopIteration:
            raise InvalidWorkflowError(f"Workflow {workflow_id} does not exist in the configuration.") from None
        else:
            permissions = wf.permissions(action, data={"parent": {"communities": {"default": community_id}}})
            return cast("bool", permissions.allows(identity))  # TODO: probable mypy bug
