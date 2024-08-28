from oarepo_ui.resources.components import UIResourceComponent
from invenio_records_resources.proxies import current_service_registry
from invenio_communities.views.communities import (
    HEADER_PERMISSIONS,
)
from flask import request


class GetCommunityComponent(UIResourceComponent):
    def before_ui_search(
        self, *, search_options, extra_context, identity, view_args, **kwargs
    ):
        community = current_service_registry.get("communities").read(
            identity, view_args["pid_value"]
        )
        request.community = community.to_dict()
        permissions = community.has_permissions_to(HEADER_PERMISSIONS)
        extra_context["community"] = community
        extra_context["permissions"] = permissions
        search_options["community"] = community.to_dict()
        search_options["overrides"]["ui_endpoint"] = (
            f"/communities/{community.id}/records"
        )
