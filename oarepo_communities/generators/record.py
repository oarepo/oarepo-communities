from collections import defaultdict

from cachetools import TTLCache, cached
from invenio_records_permissions.generators import (
    Generator,
)
from invenio_communities.generators import CommunityRoleNeed
from ..proxies import current_communities_permissions
from invenio_search.engine import dsl

class RecordCommunitiesGenerator(Generator):
    """Allows system_process role."""

    def __init__(self, action):
        self.action = action

    def needs(self, **kwargs):
        _needs = set()
        if "record" in kwargs and hasattr(kwargs["record"], "parent"):
            record = kwargs["record"]
            try:
                community_ids = record.parent["communities"]["ids"]
            except KeyError:
                return []
            by_actions = record_community_permissions(frozenset(community_ids))
            if self.action in by_actions:
                community2role_list = by_actions[self.action]
                for community_id, roles in community2role_list.items():
                    for role in roles:
                        _needs.add(CommunityRoleNeed(community_id, role))
                return _needs
        return []
    """
    def communities(self, identity):

        roles = self.roles()
        community_ids = set()
        for n in identity.provides:
            if n.method == "community" and n.role in roles:
                community_ids.add(n.value)
        return list(community_ids)

    def query_filter(self, identity=None, **kwargs):

        return dsl.Q("terms", **{"parent.communities.ids": self.communities(identity)})

    """
@cached(cache=TTLCache(maxsize=1028, ttl=600))
def record_community_permissions(record_communities):
    communities_permissions = {}

    for record_community_id in record_communities:
        communities_permissions[record_community_id] = current_communities_permissions(record_community_id)

    by_actions = defaultdict(lambda: defaultdict(list))
    for community_id, role_permissions_dct in communities_permissions.items():
        for role, role_permissions in role_permissions_dct.items():
            for action, val in role_permissions.items():
                if val:
                    by_actions[action][community_id].append(role)
    return by_actions
