from collections import defaultdict

from cachetools import TTLCache, cached
from invenio_communities.generators import CommunityRoleNeed
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl

from ..proxies import current_communities_permissions


class CommunityRolePermittedInCF(Generator):
    """Allows system_process role."""

    def __init__(self, community_permission_name):
        self.community_permission_name = community_permission_name

    def needs(self, **kwargs):
        if "record" in kwargs and hasattr(kwargs["record"], "parent"):
            record = kwargs["record"]
            try:
                community_ids = record.parent["communities"]["ids"]
            except KeyError:
                return []
        elif "community" in kwargs:
            community_ids = {kwargs["community"].id}
        else:
            return []
        return needs_from_community_ids(community_ids, self.community_permission_name)

    def query_filter(self, identity=None, **kwargs):
        allowed_communities = []
        user_communities_roles = defaultdict(set)
        if identity:
            for need in identity.provides:
                if need.method == "community":
                    user_communities_roles[need.value].add(need.role)
        permissions = record_community_permissions(frozenset(user_communities_roles.keys()))
        if self.community_permission_name in permissions:
            allowed_communities_roles = permissions[self.community_permission_name]
            for community, user_community_roles in user_communities_roles.items():
                allowed_community_roles = set(allowed_communities_roles[community])
                community_allows = bool(user_community_roles & allowed_community_roles)
                if community_allows:
                    allowed_communities.append(community)
        return dsl.Q("terms", **{"parent.communities.ids": allowed_communities})



def needs_from_community_ids(community_ids, community_permission_name):
    _needs = set()
    by_community_permission = record_community_permissions(frozenset(community_ids))
    if community_permission_name in by_community_permission:
        community2role_list = by_community_permission[community_permission_name]
        for community_id, roles in community2role_list.items():
            for role in roles:
                _needs.add(CommunityRoleNeed(community_id, role))
    return _needs


@cached(cache=TTLCache(maxsize=1028, ttl=600))
def record_community_permissions(record_communities):
    communities_permissions = {}

    for record_community_id in record_communities:
        record_community_id = str(record_community_id)
        communities_permissions[record_community_id] = current_communities_permissions(
            record_community_id
        )

    by_actions = defaultdict(lambda: defaultdict(list))
    for community_id, role_permissions_dct in communities_permissions.items():
        for role, role_permissions in role_permissions_dct.items():
            for action, val in role_permissions.items():
                if val:
                    by_actions[action][community_id].append(role)
    return by_actions
