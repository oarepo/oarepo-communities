from oarepo_global_search.ui.config import (
    GlobalSearchUIResourceConfig,
    GlobalSearchUIResource,
)
from flask_menu import current_menu
from flask_login import login_required
from oarepo_runtime.i18n import lazy_gettext as _

from .components import GetCommunityComponent

from invenio_records_resources.resources.records.resource import (
    request_read_args,
    request_search_args,
    request_view_args,
)


class CommunityRecordsUIResourceConfig(GlobalSearchUIResourceConfig):
    url_prefix = "/"
    blueprint_name = "community_records"
    template_folder = "templates"
    application_id = "community_records"
    components = [GetCommunityComponent]
    templates = {
        "search": "CommunityRecordPage",
    }

    routes = {
        "community_records": "/communities/<pid_value>",
    }
    api_service = "records"

    def search_endpoint_url(self, identity, api_config, overrides={}, **kwargs):
        community_id = kwargs.get("community", {}).get("id")

        if community_id is None:
            raise RuntimeError("Community ID is missing.")

        return f"/api/communities/{community_id}/records"


class CommunityRecordsUIResource(GlobalSearchUIResource):
    decorators = [
        login_required,
    ]

    @request_read_args
    @request_search_args
    @request_view_args
    def community_records(self):
        return self.search()


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
