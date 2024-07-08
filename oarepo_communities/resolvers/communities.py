from invenio_communities.communities.records.api import Community
from invenio_db import db
from oarepo import __version__ as oarepo_version
from invenio_records.dictutils import dict_lookup
from oarepo_workflows.permissions.generators import needs_from_generators
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_communities.records.models import CommunityWorkflowModel

from invenio_records_resources.references.entity_resolvers import (
    RecordPKProxy,
    RecordResolver,
)

from invenio_communities.communities.entity_resolvers import (
    CommunityPKProxy,
    CommunityResolver,
)
from invenio_communities.communities.entity_resolvers import CommunityRoleNeed
from invenio_communities.communities.services.config import CommunityServiceConfig


def parse_community_ref_dict_id(ref_dict):
    return ref_dict.split()[1]


class CommunityRole:

    def __init__(self, community, role):
        self.community = community
        self.role = role


class CommunityRolePKProxy(RecordPKProxy):
    # todo - list of roles perhaps?
    def _parse_ref_dict_community_role(self):
        """Parse the ID from the reference dict."""
        val = self._parse_ref_dict()[1]
        return parse_community_ref_dict_id(val)

    def _parse_ref_dict_role(self):
        """Parse the ID from the reference dict."""
        val = self._parse_ref_dict()[1]
        return val.split()[0]

    def get_needs(self, ctx=None):
        """Return community member need."""
        comid = str(self._parse_ref_dict_id())
        role = self._parse_ref_dict_role()
        return CommunityRoleNeed(comid, role)


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
            CommunityRole,
            CommunityServiceConfig.service_id,  # todo
            type_key=self.type_id,
            proxy_cls=CommunityRolePKProxy,
        )

    def _reference_entity(self, entity):
        """Create a reference dict for the given record."""
        return {self.type_key: f"{entity.community.id} : {entity.role}"}

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
