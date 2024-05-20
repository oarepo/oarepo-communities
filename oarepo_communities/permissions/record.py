from collections import defaultdict

from cachetools import TTLCache, cached
from flask_principal import Need
from invenio_access.permissions import authenticated_user
from invenio_communities.generators import CommunityRoleNeed
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl

from ..cache import allowed_communities_cache
from ..proxies import current_communities_permissions

SPECIAL_ROLES_MAPPING = {
    "authenticated_user": lambda *args, **kwargs: authenticated_user
}

SPECIAL_NEEDS_MAPPING = {
    Need(method="system_role", value="authenticated_user"): "authenticated_user",
}


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

    def _query_filter_community_needs(self, user_communities_needs):
        allowed_communities = set()
        permissions = record_community_permissions(
            frozenset(user_communities_needs.keys())
        )
        if self.community_permission_name in permissions:
            allowed_communities_roles = permissions[self.community_permission_name]
            for community, user_community_roles in user_communities_needs.items():
                allowed_community_roles = set(
                    [
                        role
                        for role in allowed_communities_roles[community]
                        if role not in SPECIAL_ROLES_MAPPING
                    ]
                )
                community_allows = bool(user_community_roles & allowed_community_roles)
                if community_allows:
                    allowed_communities.add(community)
        return allowed_communities

    def _query_filter_special_needs(self, user_needs):
        allowed_communities = set()
        # todo
        # doing search each time is possibly too expensive - user cache or some new global register?
        # for need in user_needs:
        #    allowed_communities &= globally_allowed_communities(need)
        for need in user_needs:
            if need in SPECIAL_NEEDS_MAPPING:
                allowed_communities |= allowed_communities_cache(
                    SPECIAL_NEEDS_MAPPING[need], "read"
                )
        return allowed_communities

    def query_filter(self, identity=None, **kwargs):
        user_communities_needs = defaultdict(set)
        user_general_needs = []

        if identity:
            for need in identity.provides:
                if need.method == "community":
                    user_communities_needs[need.value].add(need.role)
                else:
                    user_general_needs.append(need)

        communities_allowed_through_community_cf = self._query_filter_community_needs(
            user_communities_needs
        )
        communities_allowed_through_special_needs = self._query_filter_special_needs(
            user_general_needs
        )
        allowed_communities = (
            communities_allowed_through_community_cf
            | communities_allowed_through_special_needs
        )
        return dsl.Q("terms", **{"parent.communities.ids": list(allowed_communities)})


def needs_from_community_ids(community_ids, community_permission_name):
    needs = set()
    by_community_permission = record_community_permissions(frozenset(community_ids))
    if community_permission_name in by_community_permission:
        community2role_list = by_community_permission[community_permission_name]
        for community_id, roles in community2role_list.items():
            for role in roles:
                if role not in SPECIAL_ROLES_MAPPING:
                    needs.add(CommunityRoleNeed(community_id, role))
                else:
                    needs.add(SPECIAL_ROLES_MAPPING[role](community_id))
    return needs


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
