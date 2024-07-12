def create_oarepo_communities(app):
    """Create requests blueprint."""
    ext = app.extensions["oarepo-communities"]
    blueprint = ext.community_records_resource.as_blueprint()
    blueprint.record_once(init_addons)
    return blueprint


def init_addons(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
