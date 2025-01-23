import dataclasses

from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_records_resources.references.entity_resolvers.base import EntityResolver
from invenio_access.permissions import system_identity
from invenio_notifications.models import Recipient
from invenio_notifications.services.generators import RecipientGenerator
from invenio_records.dictutils import dict_lookup
from invenio_search.engine import dsl
from invenio_users_resources.proxies import current_users_service

from invenio_communities.proxies import current_communities
from oarepo_requests.proxies import current_oarepo_requests


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
        return {
            "community": resolved_dict.get("community"),
            "role": resolved_dict.get("role"),
            "id": resolved_dict.get("id"),
        }


class CommunityRoleResolver(EntityResolver):
    """Community entity resolver.

    The entity resolver enables Invenio-Requests to understand communities as
    receiver and topic of a request.
    """

    type_id = "community_role"
    """Type identifier for this resolver."""

    def __init__(self):
        super().__init__("community-role")

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
