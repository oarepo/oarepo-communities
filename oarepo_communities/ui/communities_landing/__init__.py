from oarepo_global_search.ui.config import (
    GlobalSearchUIResourceConfig,
    GlobalSearchUIResource,
)
from flask_menu import current_menu
from flask_login import login_required
from oarepo_runtime.i18n import lazy_gettext as _
from flask import redirect, url_for
from flask_resources import resource_requestctx
from invenio_communities.views.decorators import pass_community

from .components import GetCommunityComponent

from invenio_records_resources.resources.records.resource import (
    request_read_args,
    request_search_args,
    request_view_args,
)


class CommunityRecordsUIResourceConfig(GlobalSearchUIResourceConfig):
    url_prefix = "/communities"
    blueprint_name = "community_records"
    template_folder = "templates"
    application_id = "community_records"
    templates = {
        "search": "CommunityRecordPage",
    }

    routes = {
        "community_records": "/<pid_value>/records",
        "community_home": "/<pid_value>",
    }
    api_service = "records"

    components = [GetCommunityComponent]

    def search_endpoint_url(self, identity, api_config, overrides={}, **kwargs):
        community_id = kwargs.get("community", {}).get("id")
        print(kwargs.get("community", {}), "community_id", community_id)

        if community_id is None:
            raise RuntimeError("Community ID is missing.")

        return f"/api/communities/{community_id}/records"


# TODO: on /communities the communities listed there are linking to communities/slug, and there is actually another handler for "home" that does not seem to even be used currently
# https://github.com/inveniosoftware/invenio-app-rdm/blob/master/invenio_app_rdm/communities_ui/views/communities.py basically they are always redirecting to /communities/slug/records in its current form
# though I am not sure what this theme.enabled is supposed to be. Currently there are two handlers because of this.
class CommunityRecordsUIResource(GlobalSearchUIResource):
    decorators = [
        login_required,
    ]

    @request_read_args
    @request_search_args
    @request_view_args
    def community_records(self):
        return self.search()

    @request_read_args
    @request_search_args
    @request_view_args
    def community_home(self):
        url = url_for(
            "community_records.community_records",
            pid_value=resource_requestctx.view_args["pid_value"],
        )
        return redirect(url)


def create_blueprint(app):
    """Register blueprint for this resource."""

    app_blueprint = CommunityRecordsUIResource(
        CommunityRecordsUIResourceConfig()
    ).as_blueprint()

    @app_blueprint.before_app_first_request
    def init_menu():
        communities = current_menu.submenu("communities")
        communities.submenu("search").register(
            "community_records.community_records",
            text=_("Records"),
            order=10,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )

    return app_blueprint
