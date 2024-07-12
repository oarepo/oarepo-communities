from invenio_communities.communities.records.api import Community
from invenio_communities.generators import (
    CommunityCurators,
    CommunityMembers,
    CommunityRoleNeed,
)
from invenio_records_permissions.generators import Generator
from invenio_requests.proxies import current_requests
from oarepo_workflows import RecipientGeneratorMixin

from ..resolvers.communities import CommunityRoleObj
from ..utils import community_id_from_record, mixed_dict_lookup


class OARepoCommunityRolesMixin:
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


class CommunityRole(RecipientGeneratorMixin, OARepoCommunityRolesMixin, Generator):
    def __init__(
        self, role, access_key=None, type_key="community"
    ):  # todo access key is not always used, might be moved from here to request type, issue is that it needs to overwrite/add hooks to request type needs context

        self._access_key = access_key
        self._role = role
        self._type_key = type_key
        super().__init__()

    def roles(self, **kwargs):
        return [self._role]

    def reference_receivers(self, **kwargs):
        community_id = mixed_dict_lookup(kwargs, self._access_key)
        community = Community.pid.resolve(community_id)
        obj = CommunityRoleObj(community, self._role)
        resolver_registry = current_requests.entity_resolvers_registry
        resolver = resolver_registry._registered_types["community_role"]
        ref = resolver._reference_entity(obj)
        return [ref]


class CommunityMembers(OARepoCommunityRolesMixin, CommunityMembers):
    """"""


class CommunityCurators(OARepoCommunityRolesMixin, CommunityCurators):
    """"""
