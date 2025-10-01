#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Community role entity resolver."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast, override

from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_communities.communities.records.api import Community
from invenio_records_resources.references.entity_resolvers.base import (
    EntityProxy,
    EntityResolver,
)

from oarepo_communities.records.api import CommunityRoleRecord

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity, ItemNeed, Need

log = logging.getLogger(__name__)


class CommunityRoleProxy(EntityProxy):
    """An entity proxy for a community role."""

    @override
    def _parse_ref_dict(self) -> tuple[str, str]:
        community_id, role = self._parse_ref_dict_id().split(":")
        return community_id.strip(), role.strip()

    @override
    def _resolve(self) -> CommunityRoleRecord:
        """Resolve the Record from the proxy's reference dict."""
        community_id, role = self._parse_ref_dict()
        community = cast("Community", Community.pid.resolve(community_id))
        return CommunityRoleRecord(community, role)

    @override
    def get_needs(self, ctx: dict | None = None) -> list[Need | ItemNeed]:
        """Return community member need."""
        community_id, role = self._parse_ref_dict()
        return [CommunityRoleNeed(community_id, role)]

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict) -> dict:
        """Select which fields to return when resolving the reference."""
        return {
            "community": resolved_dict.get("community"),
            "role": resolved_dict.get("role"),
            "id": resolved_dict.get("id"),
        }


class CommunityRoleResolver(EntityResolver):
    """Community role entity resolver."""

    type_id = "community_role"
    """Type identifier for this resolver."""

    def __init__(self):
        """Create the resolver."""
        super().__init__("community-role")

    @override
    def _reference_entity(self, entity: Any) -> dict[str, str]:
        """Create a reference dict for the given record."""
        return {"community_role": f"{entity.community_id}:{entity.role}"}

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity is a record."""
        return isinstance(entity, CommunityRoleRecord)

    @override
    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dict references a request."""
        return "community_role" in ref_dict

    @override
    def _get_entity_proxy(self, ref_dict: dict) -> CommunityRoleProxy:
        """Return a RecordProxy for the given reference dict."""
        return CommunityRoleProxy(self, ref_dict)
