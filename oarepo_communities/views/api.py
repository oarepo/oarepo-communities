def create_oarepo_communities(app):
    """Create requests blueprint."""
    ext = app.extensions["oarepo-communities"]
    blueprint = ext.community_records_resource.as_blueprint()
    return blueprint

