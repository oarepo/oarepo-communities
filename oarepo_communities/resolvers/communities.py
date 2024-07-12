from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.services.config import CommunityServiceConfig
from invenio_records_resources.references.entity_resolvers import (
    RecordPKProxy,
    RecordResolver,
)
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound


def parse_community_ref_dict_community_id(ref_dict):
    return ref_dict.split(":")[0].strip()


def parse_community_ref_dict_role(ref_dict):
    return ref_dict.split(":")[1].strip()


class CommunityRoleObj:
    community_cls = Community

    def __init__(self, community, role):
        self.community = community
        self.role = role

    @classmethod
    def get_record(cls, id_):
        # todo this should return communityroleobj, but since it's not saved in neither db nor search (fix this?)
        return cls.community_cls.get_record(id_)


class CommunityRolePKProxy(RecordPKProxy):
    # todo - list of roles perhaps?
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
        return parse_community_ref_dict_community_id(val)

    def _parse_ref_dict_role(self):
        """Parse the ID from the reference dict."""
        val = self._parse_ref_dict_id()
        return parse_community_ref_dict_role(val)

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


# todo should test with community as receiver, now everything gets community role
"""
class OARepoCommunityPKProxy(CommunityPKProxy):
    def _parse_ref_dict_id(self):
        val = self._parse_ref_dict()[1]
        return parse_community_ref_dict_id(val)

    def _parse_ref_dict_workflow(self):
        val = self._parse_ref_dict()[1]
        return val.split()[0]

    def get_needs(self, ctx=None):
        comm_id = self._parse_ref_dict_id()
        workflow_id = self._parse_ref_dict_workflow()
        if not workflow_id:
            workflow_id = (
                db.session.query(CommunityWorkflowModel.workflow)
                .filter(CommunityWorkflowModel.community_id == comm_id)
                .one()
            )

        # todo i can save workflow id into refdict encoding and request type into ctx (if it's always called with the same ctx)
        # needs from generators might still need reference to topic?

        # this expects the reference to always happen with the context of requests, is that reasonable?

        generators = dict_lookup(
            current_oarepo_workflows.record_workflows, f"{workflow_id}.requests.{ctx['request_type']}.recipients"
        )
        needs = needs_from_generators(generators, community_id=comm_id)
        return needs


class CommunityResolver(RecordResolver):


    type_id = "community"


    def __init__(self):

        super().__init__(
            Community,
            CommunityServiceConfig.service_id,
            type_key=self.type_id,
            proxy_cls=CommunityPKProxy,
        )

    def _reference_entity(self, entity):

        return {self.type_key: str(entity.id)}


class OARepoCommunityResolver(CommunityResolver):
    type_id = "community"

    def __init__(self):

        super(CommunityResolver, self).__init__(
            Community,
            CommunityServiceConfig.service_id,
            type_key=self.type_id,
            proxy_cls=OARepoCommunityPKProxy,
        )

    def _reference_entity(self, entity):

        assert hasattr(entity, "workflow_id")
        return {self.type_key: f"{entity.workflow_id} {entity.id}"}
    """
