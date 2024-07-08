from invenio_search.engine import dsl
from invenio_records_permissions.generators import Generator
from invenio_communities.proxies import current_roles
from invenio_communities.generators import CommunityRoleNeed

from invenio_requests.services.generators import Receiver
from oarepo_requests.utils import get_from_requests_workflow, workflow_from_record
from oarepo_workflows.permissions.generators import needs_from_generators, \
    reference_receiver_from_generators

from ..utils import community_id_from_record, mixed_dict_lookup


# todo add workflow ids into reference

class CommunityInTopicReceiver(Receiver):
    def ref(self, **kwargs):
        topic = kwargs["record"]
        return {"community": str(topic.parent.communities.default.id)}

class CommunityInPayloadReceiver(Receiver):
    def ref(self, **kwargs):
        data = kwargs["data"]
        target_community = data["payload"]["community"]
        return {"community": target_community}

class CommunityReceiver(Receiver):
    def __init__(self, access_key, role, type_key="community"):
        """Initialize need entity generator."""
        self._access_key = access_key
        self._role = role
        self._type_key = type_key
        super().__init__()

    def reference_receiver(self, **kwargs):
        from invenio_communities.communities.records.api import Community

        community_id = mixed_dict_lookup(kwargs, self._access_key)
        community = Community.pid.resolve(community_id)
        topic = kwargs["record"]
        workflow_id = workflow_from_record(topic)
        community.workflow_id = workflow_id

        from invenio_requests.proxies import current_requests
        resolver_registry = current_requests.entity_resolvers_registry
        resolver = resolver_registry._registered_types["community"]
        ref = resolver._reference_entity(community)
        return ref

    def needs(self, community_id=None, **kwargs):
        return [CommunityRoleNeed(community_id, self._role)]


"""
class CommunityReceiver(Receiver):

    def ref(self, **kwargs):
        access_key = kwargs["request_type"] # maybe??; if we already have predefined payloads, then it might make sense?
        target_community = dict_lookup(kwargs, access_key)
        return {"community": target_community}
"""

class RecipientsFromWorkflow(Generator):
    def _get_workflow_id(self, request_type, *args, **kwargs):
        # todo move into outside function
        if "record" in kwargs:
            return kwargs["record"].parent["workflow"]
        return "default"
    def needs(self, request_type, **kwargs):
        # todo load from community
        workflow_id = self._get_workflow_id(request_type, **kwargs)
        try:
            recipients_generators = get_from_requests_workflow(workflow_id, request_type.type_id, "recipients")
        except KeyError:
            return []
        needs = needs_from_generators(recipients_generators, request_type=request_type, **kwargs)
        return needs

    """
    def ref(self, request_type=None, **kwargs):
        workflow_id = self._get_workflow_id(request_type, **kwargs)
        try:
            recipients_generators = get_from_requests_workflow(workflow_id, request_type.type_id, "recipients")
        except KeyError:
            return None
        return reference_receiver_from_generators(recipients_generators, request_type=request_type, **kwargs)
    """
    # todo query_filter?


class CommunityRole(Generator):

    def __init__(self, role):
        self.role = role

    def roles(self, **kwargs):
        return [self.role]

    def communities(self, identity):

        raise NotImplementedError

    def needs(self, record=None, community_id=None, **kwargs):
        if not community_id:
            community_id = community_id_from_record(record)
        if not community_id:
            print("No community id provided.")
            return []

        assert community_id, "No community id provided."
        community_id = str(community_id)

        roles = self.roles(**kwargs)
        if roles:
            needs = [CommunityRoleNeed(community_id, role) for role in roles]
            return needs
        return []

    """
    def query_filter(self, identity=None, **kwargs):
        # Gives access to all community members.
        return dsl.Q("terms", **{"_id": self.communities(identity)})
    """

class CommunityRoles(Generator):
    """Base class for community roles generators."""

    def roles(self, **kwargs):
        """R."""
        raise NotImplementedError

    def communities(self, identity):
        """Communities."""
        raise NotImplementedError

    def needs(self, record=None, community_id=None, **kwargs):
        """Enabling Needs."""
        if not community_id:
            community_id = community_id_from_record(record)
        if not community_id:
            print("No community id provided.")
            return []

        community_id = str(community_id)

        roles = self.roles(**kwargs)
        if roles:
            needs = [CommunityRoleNeed(community_id, role) for role in roles]
            return needs
        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # Gives access to all community members.
        return dsl.Q("terms", **{"_id": self.communities(identity)})


class CommunityMembers(CommunityRoles):
    """Roles representing all members of a community."""

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles]

    def communities(self, identity):
        """Communities."""
        return [n.value for n in identity.provides if n.method == "community"]


class CommunityCurators(CommunityRoles):
    """Roles representing all curators of a community."""

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles.can("curate")]
