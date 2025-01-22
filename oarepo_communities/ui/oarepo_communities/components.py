from flask import request
from invenio_communities.views.communities import HEADER_PERMISSIONS
from oarepo_ui.resources.components import UIResourceComponent


class GetCommunityComponent(UIResourceComponent):
    def before_ui_search(
        self, *, search_options, extra_context, identity, view_args, **kwargs
    ):
        community = view_args.get("community")
        community_id = str(community.id)

        workflow_name = community["custom_fields"].get("workflow", "default")
        from oarepo_workflows.errors import InvalidWorkflowError
        from oarepo_workflows.proxies import current_oarepo_workflows

        if workflow_name not in current_oarepo_workflows.record_workflows:
            raise InvalidWorkflowError(
                f"Workflow {workflow_name} does not exist in the configuration."
            )

        workflow = current_oarepo_workflows.record_workflows[workflow_name]
        permissions = workflow.permissions(
            "create", data={"parent": {"communities": {"default": community_id}}}
        )
        can_create_record = permissions.allows(identity)

        # for consistency with invenio-communities routes
        # needed to check if there is something in the curation policy and
        # about page, so that those tabs would render in the menu
        request.community = community.to_dict()
        permissions = community.has_permissions_to(HEADER_PERMISSIONS)
        permissions["can_create_record"] = can_create_record
        extra_context["community"] = community
        extra_context["permissions"] = permissions
        search_options["overrides"][
            "ui_endpoint"
        ] = f"/communities/{community_id}/records"
