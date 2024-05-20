from oarepo_communities.resolvers.communities import OARepoCommunityResolver


def create_oarepo_communities(app):
    """Create requests blueprint."""
    ext = app.extensions["oarepo-communities"]
    blueprint = ext.community_records_resource.as_blueprint()
    blueprint.record_once(init_addons_thesis_requests)
    return blueprint


def init_addons_thesis_requests(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
    resolvers._registered_types["community"] = OARepoCommunityResolver()
