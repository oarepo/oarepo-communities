from flask import Blueprint


def create_app_blueprint(app):
    blueprint = Blueprint("oarepo_communities_app", __name__, url_prefix="/communities/")
    return blueprint
