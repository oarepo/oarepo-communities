from invenio_records_permissions.generators import SystemProcess
from invenio_requests.services.permissions import PermissionPolicy
from oarepo_requests.permissions.generators import CreatorsFromWorkflow

from oarepo_communities.resolvers.communities import OARepoCommunityResolver


def create_oarepo_communities(app):
    """Create requests blueprint."""
    ext = app.extensions["oarepo-communities"]
    blueprint = ext.community_records_resource.as_blueprint()
    blueprint.record_once(init_addons)
    return blueprint


def init_addons(state):
    app = state.app

    resolvers = app.extensions["invenio-requests"].entity_resolvers_registry
    resolvers._registered_types["community"] = OARepoCommunityResolver()

    # todo hack; doesn't seem to work
    """
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

    setattr(app.extensions["invenio-requests"].requests_service.config, "permission_policy_cls", permissions)
    print()
    """
