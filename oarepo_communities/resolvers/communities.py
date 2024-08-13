import dataclasses

from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_records_resources.references.entity_resolvers.base import EntityResolver


@dataclasses.dataclass
class CommunityRoleObj:
    community_id: str
    role: str


from invenio_records_resources.references.entity_resolvers.base import EntityProxy


class CommunityRoleProxy(EntityProxy):
    def _parse_ref_dict(self):
        community_id, role = self._parse_ref_dict_id().split(":")
        return community_id.strip(), role.strip()

    def _resolve(self):
        """Resolve the Record from the proxy's reference dict."""
        community_id, role = self._parse_ref_dict()

        return CommunityRoleObj(community_id, role)

    def get_needs(self, ctx=None):
        """Return community member need."""
        community_id, role = self._parse_ref_dict()
        return [CommunityRoleNeed(community_id, role)]

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        return {"community_role": resolved_dict.get("community_role")}


class CommunityRoleResolver(EntityResolver):
    """Community entity resolver.

    The entity resolver enables Invenio-Requests to understand communities as
    receiver and topic of a request.
    """

    type_id = "community_role"
    """Type identifier for this resolver."""

    def __init__(self):
        super().__init__(None)

    def _reference_entity(self, entity: CommunityRoleObj):
        """Create a reference dict for the given record."""
        return {"community_role": f"{entity.community_id}:{entity.role}"}

    def matches_entity(self, entity):
        """Check if the entity is a record."""
        return isinstance(entity, CommunityRoleObj)

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a request."""
        return "community_role" in ref_dict

    def _get_entity_proxy(self, ref_dict):
        """Return a RecordProxy for the given reference dict."""
        return CommunityRoleProxy(self, ref_dict)
