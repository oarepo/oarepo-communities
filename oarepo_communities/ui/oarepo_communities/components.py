from flask import request
from invenio_communities.views.communities import HEADER_PERMISSIONS
from oarepo_ui.resources.components import UIResourceComponent


class GetCommunityComponent(UIResourceComponent):
    def before_ui_search(
        self, *, search_options, extra_context, identity, view_args, **kwargs
    ):
        community = view_args.get("community")
        # for consistency with invenio-communities routes
        # needed to check if there is something in the curation policy and
        # about page, so that those tabs would render in the menu
        request.community = community.to_dict()
        permissions = community.has_permissions_to(HEADER_PERMISSIONS)
        extra_context["community"] = community
        extra_context["permissions"] = permissions
        search_options["overrides"][
            "ui_endpoint"
        ] = f"/communities/{community.id}/records"
