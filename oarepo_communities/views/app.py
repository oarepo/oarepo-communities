from flask import Blueprint

from oarepo_communities.resolvers.communities import OARepoCommunityResolver


def create_app_blueprint(app):
    blueprint = Blueprint(
        "oarepo_communities_app", __name__, url_prefix="/communities/"
    )
    blueprint.record_once(init_addons_thesis_requests)
    return blueprint


def init_addons_thesis_requests(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
    resolvers._registered_types["community"] = OARepoCommunityResolver()
