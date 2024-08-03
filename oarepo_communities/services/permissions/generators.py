from invenio_communities.communities.records.api import Community
from invenio_communities.generators import (
    CommunityCurators,
    CommunityMembers,
    CommunityRoleNeed,
)
from invenio_records_permissions.generators import Generator
from invenio_requests.proxies import current_requests
from oarepo_workflows.requests.policy import RecipientGeneratorMixin

from oarepo_communities.resolvers.communities import CommunityRoleObj
from oarepo_communities.utils import community_id_from_record, dict_obj_lookup


class OARepoCommunityRolesMixin:
    # Invenio generators do not capture all situations where we need community id from record
    def needs(self, record=None, community_id=None, **kwargs):

        if not community_id:
            community_id = community_id_from_record(record)
        community_id = str(community_id)
        if not community_id:
            print("No community id provided.")
            return []

        roles = self.roles(**kwargs)
        if roles:
            needs = [CommunityRoleNeed(community_id, role) for role in roles]
            return needs
        return []


class CommunityRole(RecipientGeneratorMixin, OARepoCommunityRolesMixin, Generator):
    access_key = "record.parent.communities.default.id"

    def __init__(self, role, type_key="community"):
        self._role = role
        self._type_key = type_key
        super().__init__()

    def roles(self, **kwargs):
        return [self._role]

    def reference_receivers(self, **kwargs):
        community_id = dict_obj_lookup(kwargs, self.access_key)
        community = Community.pid.resolve(community_id)
        obj = CommunityRoleObj(community, self._role)
        resolver_registry = current_requests.entity_resolvers_registry
        resolver = resolver_registry._registered_types["community_role"]
        ref = resolver._reference_entity(obj)
        return [ref]


class TargetCommunityRole(CommunityRole):
    access_key = "data.payload.community"


class CommunityMembers(OARepoCommunityRolesMixin, CommunityMembers):
    """"""


class CommunityCurators(OARepoCommunityRolesMixin, CommunityCurators):
    """"""
