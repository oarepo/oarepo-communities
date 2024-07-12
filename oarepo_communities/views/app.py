from flask import Blueprint


def create_app_blueprint(app):
    blueprint = Blueprint(
        "oarepo_communities_app", __name__, url_prefix="/communities/"
    )
    blueprint.record_once(init_addons)
    return blueprint


def init_addons(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
