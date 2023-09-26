from collections import defaultdict

from cachetools import TTLCache, cached
from invenio_records_permissions.generators import (
    Generator,
)
from invenio_communities.generators import CommunityRoleNeed
from ..proxies import current_communities_permissions


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
                for c, roles in community2role_list.items():
                    for role in roles:
                        _needs.add(CommunityRoleNeed(c, role))
                return _needs
        return []


@cached(cache=TTLCache(maxsize=1028, ttl=360))
def record_community_permissions(record_communities):
    communities_permissions = {}

    for record_community_id in record_communities:
        communities_permissions[record_community_id] = current_communities_permissions(record_community_id)

    by_actions = defaultdict(lambda: defaultdict(list))
    for c, role_permissions_dct in communities_permissions.items():
        for role, role_permissions in role_permissions_dct.items():
            for action, val in role_permissions.items():
                if val:
                    by_actions[action][c].append(role)
    return by_actions
