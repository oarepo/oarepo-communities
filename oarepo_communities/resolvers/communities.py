from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_records_resources.references.entity_resolvers.base import EntityResolver

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity, Need


@dataclasses.dataclass
class CommunityRoleObj:
    community_id: str
    role: str


from invenio_records_resources.references.entity_resolvers.base import EntityProxy


class CommunityRoleProxy(EntityProxy):
    def _parse_ref_dict(self) -> tuple[str, str]:
        community_id, role = self._parse_ref_dict_id().split(":")
        return community_id.strip(), role.strip()

    def _resolve(self) -> CommunityRoleObj:
        """Resolve the Record from the proxy's reference dict."""
        community_id, role = self._parse_ref_dict()

        return CommunityRoleObj(community_id, role)

    def get_needs(self, ctx: dict | None = None) -> list[Need]:
        """Return community member need."""
        community_id, role = self._parse_ref_dict()
        return [CommunityRoleNeed(community_id, role)]

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
        super().__init__("community-role")

    def _reference_entity(self, entity: Any) -> dict[str, str]:
        """Create a reference dict for the given record."""
        return {"community_role": f"{entity.community_id}:{entity.role}"}

    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity is a record."""
        return isinstance(entity, CommunityRoleObj)

    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dict references a request."""
        return "community_role" in ref_dict

    def _get_entity_proxy(self, ref_dict: dict) -> CommunityRoleProxy:
        """Return a RecordProxy for the given reference dict."""
        return CommunityRoleProxy(self, ref_dict)
