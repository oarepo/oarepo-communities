from oarepo_global_search.ui.config import (
    GlobalSearchUIResourceConfig,
    GlobalSearchUIResource,
)
from flask import g
from flask_menu import current_menu
from flask_login import login_required
from oarepo_runtime.i18n import lazy_gettext as _
from flask import redirect, url_for
from flask_resources import resource_requestctx
from invenio_communities.views.communities import (
    communities_settings as invenio_communities_settings,
    communities_settings_curation_policy as invenio_communities_settings_curation_policy,
    communities_settings_privileges as invenio_communities_settings_privileges,
    communities_settings_pages as invenio_communities_settings_pages,
    members as invenio_communities_members,
    communities_curation_policy as invenio_communities_curation_policy,
    communities_about as invenio_communities_about,
)

from invenio_communities.views.ui import (
    _has_about_page_content,
    _has_curation_policy_page_content,
    _show_create_community_link,
)
from invenio_records_resources.proxies import current_service_registry

from .components import GetCommunityComponent

from invenio_records_resources.resources.records.resource import (
    request_read_args,
    request_search_args,
    request_view_args,
)


class CommunityRecordsUIResourceConfig(GlobalSearchUIResourceConfig):
    url_prefix = "/communities"
    blueprint_name = "invenio_communities"
    template_folder = "templates"
    application_id = "community_records"
    templates = {
        "search": "CommunityRecordPage",
    }

    routes = {
        "community_records": "/<pid_value>/records",
        "community_home": "/<pid_value>",
        "communities_settings": "/<pid_value>/settings",
        "communities_settings_privileges": "/<pid_value>/settings/privileges",
        "communities_settings_curation_policy": "/<pid_value>/settings/curation_policy",
        "communities_settings_pages": "/<pid_value>/settings/pages",
        "members": "/<pid_value>/members",
        "communities_curation_policy": "/<pid_value>/curation_policy",
        "communities_about": "/<pid_value>/about",
        "invitations": "/<pid_value>/invitations",
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

    @request_view_args
    def communities_settings(
        self,
    ):
        return invenio_communities_settings(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def communities_settings_privileges(
        self,
    ):
        return invenio_communities_settings_privileges(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def communities_settings_curation_policy(
        self,
    ):
        return invenio_communities_settings_curation_policy(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def communities_settings_pages(
        self,
    ):
        return invenio_communities_settings_pages(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def members(
        self,
    ):
        return invenio_communities_members(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def communities_curation_policy(
        self,
    ):
        return invenio_communities_curation_policy(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    @request_view_args
    def communities_about(
        self,
    ):
        return invenio_communities_about(
            pid_value=resource_requestctx.view_args["pid_value"]
        )

    def invitations(self):
        return self.members()


def create_blueprint(app):
    """Register blueprint for this resource."""

    app_blueprint = CommunityRecordsUIResource(
        CommunityRecordsUIResourceConfig()
    ).as_blueprint()

    @app_blueprint.before_app_first_request
    def init_menu():
        communities = current_menu.submenu("communities")
        communities.submenu("search").register(
            "invenio_communities.community_records",
            text=_("Records"),
            order=10,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )
        communities.submenu("members").register(
            endpoint="invenio_communities.members",
            text=_("Members"),
            order=30,
            expected_args=["pid_value"],
            **{"icon": "users", "permissions": "can_members_search_public"},
        )

        communities.submenu("settings").register(
            endpoint="invenio_communities.communities_settings",
            text=_("Settings"),
            order=40,
            expected_args=["pid_value"],
            **{"icon": "settings", "permissions": "can_update"},
        )

        communities.submenu("curation_policy").register(
            endpoint="invenio_communities.communities_curation_policy",
            text=_("Curation policy"),
            order=50,
            visible_when=_has_curation_policy_page_content,
            expected_args=["pid_value"],
            **{"icon": "balance scale", "permissions": "can_read"},
        )
        communities.submenu("about").register(
            endpoint="invenio_communities.communities_about",
            text=_("About"),
            order=60,
            visible_when=_has_about_page_content,
            expected_args=["pid_value"],
            **{"icon": "info", "permissions": "can_read"},
        )

    return app_blueprint
