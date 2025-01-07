import marshmallow as ma
from flask import g, redirect, url_for
from flask_menu import current_menu
from flask_resources import from_conf, request_parser, resource_requestctx
from invenio_communities.communities.resources.serializer import (
    UICommunityJSONSerializer,
)
from invenio_communities.views.communities import (
    communities_about as invenio_communities_about,
)
from invenio_communities.views.communities import (
    communities_curation_policy as invenio_communities_curation_policy,
)
from invenio_communities.views.communities import (
    communities_frontpage as invenio_communities_frontpage,
)
from invenio_communities.views.communities import (
    communities_new as invenio_communities_new,
)
from invenio_communities.views.communities import (
    communities_search as invenio_communities_search,
)
from invenio_communities.views.communities import (
    communities_settings as invenio_communities_settings,
)
from invenio_communities.views.communities import (
    communities_settings_pages as invenio_communities_settings_pages,
)
from invenio_communities.views.communities import members as invenio_communities_members
from invenio_communities.views.ui import (
    _has_about_page_content,
    _has_curation_policy_page_content,
)
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.resources.records.resource import request_view_args
from oarepo_global_search.ui.config import (
    GlobalSearchUIResource,
    GlobalSearchUIResourceConfig,
)
from oarepo_runtime.i18n import lazy_gettext as _

from .components import GetCommunityComponent


class CommunityValidationSchema(ma.Schema):
    pid_value = ma.fields.String()

    def load(self, data, *args, **kwargs):
        pid_value = data.get("pid_value")

        community = current_service_registry.get("communities").read(
            g.identity, pid_value
        )
        UICommunityJSONSerializer().dump_obj(community.to_dict())
        return {"community": community}


request_community_view_args = request_parser(
    from_conf("request_community_view_args"), location="view_args"
)


class CommunityRecordsUIResourceConfig(GlobalSearchUIResourceConfig):
    url_prefix = "/communities"
    blueprint_name = "oarepo_communities"
    template_folder = "templates"
    application_id = "community_records"
    templates = {
        "search": "CommunityRecordsPage",
    }
    request_community_view_args = CommunityValidationSchema

    routes = {
        "community_records": "/<pid_value>/records",
        "community_home": "/<pid_value>",
        "communities_settings": "/<pid_value>/settings",
        "communities_settings_pages": "/<pid_value>/settings/pages",
        "members": "/<pid_value>/members",
        "communities_curation_policy": "/<pid_value>/curation_policy",
        "communities_about": "/<pid_value>/about",
        "communities_frontpage": "/",
        "communities_search": "/search",
        "communities_new": "/new",
    }
    api_service = "records"

    components = [GetCommunityComponent]

    def search_endpoint_url(self, identity, api_config, overrides={}, **kwargs):
        community_id = resource_requestctx.view_args["community"].to_dict()["id"]
        return f"/api/communities/{community_id}/records"


class CommunityRecordsUIResource(GlobalSearchUIResource):
    @request_view_args
    @request_community_view_args
    def community_records(self):
        return self.search()

    @request_view_args
    @request_community_view_args
    def community_home(self):
        url = url_for(
            "oarepo_communities.community_records",
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

    def communities_frontpage(self):
        return invenio_communities_frontpage()

    def communities_search(self):
        return invenio_communities_search()

    def communities_new(self):
        return invenio_communities_new()


def create_blueprint(app):
    """Register blueprint for this resource."""

    app_blueprint = CommunityRecordsUIResource(
        CommunityRecordsUIResourceConfig()
    ).as_blueprint()

    @app_blueprint.before_app_first_request
    def init_menu():
        current_menu.submenu("main.communities").register(
            endpoint="oarepo_communities.communities_frontpage",
            text=_("Communities"),
            order=0,
        )
        communities = current_menu.submenu("communities")
        communities.submenu("search").register(
            "oarepo_communities.community_records",
            text=_("Records"),
            order=10,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )
        communities.submenu("members").register(
            endpoint="oarepo_communities.members",
            text=_("Members"),
            order=30,
            expected_args=["pid_value"],
            **{"icon": "users", "permissions": "can_members_search_public"},
        )

        communities.submenu("settings").register(
            endpoint="oarepo_communities.communities_settings",
            text=_("Settings"),
            order=40,
            expected_args=["pid_value"],
            **{"icon": "settings", "permissions": "can_update"},
        )

        communities.submenu("curation_policy").register(
            endpoint="oarepo_communities.communities_curation_policy",
            text=_("Curation policy"),
            order=50,
            visible_when=_has_curation_policy_page_content,
            expected_args=["pid_value"],
            **{"icon": "balance scale", "permissions": "can_read"},
        )
        communities.submenu("about").register(
            endpoint="oarepo_communities.communities_about",
            text=_("About"),
            order=60,
            visible_when=_has_about_page_content,
            expected_args=["pid_value"],
            **{"icon": "info", "permissions": "can_read"},
        )

    return app_blueprint
