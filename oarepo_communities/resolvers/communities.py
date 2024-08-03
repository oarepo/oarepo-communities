from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.services.config import CommunityServiceConfig
from invenio_records_resources.references.entity_resolvers import (
    RecordPKProxy,
    RecordResolver,
)
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound


class CommunityRoleObj:
    community_cls = Community

    def __init__(self, community, role):
        self.community = community
        self.role = role

    @classmethod
    def get_record(cls, id_):
        # todo this should return communityroleobj, but since it's not saved in neither db nor search (fix this?)
        return cls.community_cls.get_record(id_)

    @classmethod
    def community_role_or_community_ref_get_community_id(cls, ref_value):
        return ref_value.split(":")[0].strip()

    @classmethod
    def community_role_ref_get_role(cls, ref_value):
        return ref_value.split(":")[1].strip()


class CommunityRolePKProxy(RecordPKProxy):

    def _resolve(self):
        """Resolve the Record from the proxy's reference dict."""
        id_ = self._parse_ref_dict_community_id()
        role = self._parse_ref_dict_role()
        try:
            community = self.record_cls.get_record(id_)
            return CommunityRoleObj(community, role)
        except StatementError as exc:
            raise NoResultFound() from exc

    def _parse_ref_dict_community_id(self):
        """Parse the ID from the reference dict."""
        val = self._parse_ref_dict_id()
        return CommunityRoleObj.community_role_or_community_ref_get_community_id(val)

    def _parse_ref_dict_role(self):
        """Parse the ID from the reference dict."""
        val = self._parse_ref_dict_id()
        return CommunityRoleObj.community_role_ref_get_role(val)

    def get_needs(self, ctx=None):
        """Return community member need."""
        comid = self._parse_ref_dict_community_id()
        role = self._parse_ref_dict_role()
        return [CommunityRoleNeed(comid, role)]

    def community_reference(self):
        return {"community": self._parse_ref_dict_community_id()}


class CommunityRoleResolver(RecordResolver):
    """Community entity resolver.

    The entity resolver enables Invenio-Requests to understand communities as
    receiver and topic of a request.
    """

    type_id = "community_role"
    """Type identifier for this resolver."""

    def __init__(self):
        """Initialize the default record resolver."""
        super().__init__(
            CommunityRoleObj,
            CommunityServiceConfig.service_id,
            type_key=self.type_id,
            proxy_cls=CommunityRolePKProxy,
        )

    def _reference_entity(self, entity):
        """Create a reference dict for the given record."""
        return {self.type_key: f"{entity.community.id} : {entity.role}"}
