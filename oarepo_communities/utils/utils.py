from invenio_records_resources.proxies import current_service_registry
from invenio_requests.resolvers.registry import ResolverRegistry


# todo cache? would have to be done by using record cls as key
def get_matching_service(record):
    for resolver in ResolverRegistry.get_registered_resolvers():
        if resolver.matches_entity(record):
            return current_service_registry.get(resolver._service_id)
    return None


"""
def get_allowed_actions(record, identity=None):
    record_communities = set(record["parent"]["communities"]["ids"])

    user_community_roles = defaultdict(list)
    communities_permissions = {}

    for record_community_id in record_communities:
        if need.method == "community" and need.value in record_communities:
    for need in identity.provides:

            user_community_roles[need.value].append(need.role)
            communities_permissions[need.value] = \
                current_communities_permissions(need.value)

    allowed_actions_for_record_and_user = set()
    for user_community, user_roles_community in user_community_roles.items():
        if user_community in record_communities:
            for user_role_community in user_roles_community:
                permissions = communities_permissions[user_community][user_role_community]
                allowed_actions_for_record_and_user |= {permission for permission, allowed in permissions.items() if
                                                        allowed}
                """
