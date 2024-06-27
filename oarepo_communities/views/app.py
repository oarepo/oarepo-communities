from flask import Blueprint
from invenio_records_permissions.generators import SystemProcess
from invenio_requests.services.permissions import PermissionPolicy
from oarepo_requests.permissions.generators import CreatorsFromWorkflow

from oarepo_communities.resolvers.communities import OARepoCommunityResolver

def create_app_blueprint(app):
    blueprint = Blueprint(
        "oarepo_communities_app", __name__, url_prefix="/communities/"
    )
    blueprint.record_once(init_addons)
    return blueprint


def init_addons(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
    resolvers._registered_types["community"] = OARepoCommunityResolver()

    # todo hack
    permissions = type(
        "RequestsPermissionPolicy",
        (PermissionPolicy,),
        dict(
            can_create=[
                SystemProcess(),
                CreatorsFromWorkflow(),
            ],
        ),
    )
    app.extensions["invenio-requests"].requests_service.config.permission_policy_cls = (
        permissions
    )
