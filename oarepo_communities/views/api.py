from oarepo_communities.resolvers.communities import CommunityRoleResolver


def create_oarepo_communities(app):
    # Do we need to add this to service registry?
    # - use similar pattern like in invenio-requests etc? finalize app and api-finalize-app in entrypoints?
    ext = app.extensions["oarepo-communities"]
    blueprint = ext.community_records_resource.as_blueprint()
    blueprint.record_once(register_community_role_entity_resolver)
    return blueprint


def register_community_role_entity_resolver(
    state,
):  # todo consider using different method for registering the resolver

    app = state.app
    requests = app.extensions["invenio-requests"]
    requests.entity_resolvers_registry.register_type(CommunityRoleResolver())
