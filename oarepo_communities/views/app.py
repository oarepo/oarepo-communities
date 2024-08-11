from flask import Blueprint

from oarepo_communities.resolvers.communities import CommunityRoleResolver


def create_app_blueprint(app):
    blueprint = Blueprint(
        "oarepo_communities_app", __name__, url_prefix="/communities/"
    )
    blueprint.record_once(register_community_role_entity_resolver)
    return blueprint


def register_community_role_entity_resolver(state):

    app = state.app
    requests = app.extensions["invenio-requests"]
    requests.entity_resolvers_registry.register_type(CommunityRoleResolver())
