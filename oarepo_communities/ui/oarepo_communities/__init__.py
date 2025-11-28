#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""oarepo-communities ui package."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

from flask import request
from flask_menu import current_menu
from invenio_app_rdm.ext import _is_branded_community, _show_browse_page
from oarepo_ui.overrides import (
    UIComponent,
    UIComponentOverride,
)
from oarepo_ui.overrides.components import DisabledComponent, UIComponentImportMode
from oarepo_ui.proxies import current_ui_overrides
from oarepo_ui.resources.template_pages import (
    TemplatePageUIResource,
    TemplatePageUIResourceConfig,
)

if TYPE_CHECKING:
    from flask import Blueprint, Flask


communities_detail_endpoint = "invenio_app_rdm_communities.communities_detail"


class ComponentsResourceConfig(TemplatePageUIResourceConfig):
    """oarepo-communities resource config."""

    url_prefix = "/communities"
    blueprint_name = "communities_dummy_blueprint"
    template_folder = "templates"


def _register_community_uploads_result_item(
    ui_overrides: set[UIComponentOverride], schema: str, component: UIComponent
) -> None:
    """Register a result list items for dashboard uploads."""
    community_uploads_result_list_item = UIComponentOverride(  # pragma: no cover
        communities_detail_endpoint,
        f"InvenioCommunities.DetailsSearch.ResultsList.item.{schema}",
        component,
    )
    if community_uploads_result_list_item not in ui_overrides:  # pragma: no cover
        ui_overrides.add(community_uploads_result_list_item)


overrides_list = []
dynamic_result_list_item = UIComponent(
    "DynamicResultsListItem",
    "@js/oarepo_ui/search/DynamicResultsListItem",
    UIComponentImportMode.DEFAULT,
)
overrides_list.append(
    UIComponentOverride(
        communities_detail_endpoint,
        "InvenioCommunities.DetailsSearch.ResultsList.item",
        dynamic_result_list_item,
    )
)

search_bar = UIComponent(
    "ClearableSearchbarElement",
    "@js/oarepo_ui/search/ClearableSearchbarElement",
    UIComponentImportMode.NAMED,
)
overrides_list.append(
    UIComponentOverride(
        communities_detail_endpoint,
        "InvenioCommunities.DetailsSearch.SearchBar.element",
        search_bar,
    )
)
overrides_list.append(
    UIComponentOverride(
        "invenio_communities.communities_settings",
        "InvenioCommunities.CommunityProfileForm.GridRow.DangerZone",
        DisabledComponent,
    )
)
community_invitation_modal = UIComponent(
    "CommunityInvitationsModal",
    "@js/oarepo_communities/components/CommunityInvitationsModal",
    UIComponentImportMode.NAMED,
)
overrides_list.append(
    UIComponentOverride(
        "invenio_communities.members",
        "InvenioCommunities.CommunityMembers.InvitationsModal",
        community_invitation_modal,
    )
)

overrides_list.append(
    UIComponentOverride(
        "invenio_communities.invitations",
        "InvenioCommunities.CommunityMembers.InvitationsModal",
        community_invitation_modal,
    )
)


def ui_overrides(app: Flask) -> None:  # NOQA: ARG001
    """Define overrides that this library will register."""
    for override in overrides_list:
        if override not in current_ui_overrides:
            current_ui_overrides.add(override)


def create_blueprint(app: Flask) -> Blueprint:
    """Register blueprint for this resource."""
    app.config.get("OAREPO_UI_RESULT_LIST_ITEM_REGISTRATION_CALLBACKS", []).append(
        _register_community_uploads_result_item
    )
    return TemplatePageUIResource(ComponentsResourceConfig()).as_blueprint()  # type: ignore[reportArgumentType]


def init_menu(app: Flask) -> None:  # NOQA: ARG001
    """Initialize menu."""
    communities = current_menu.submenu("communities")
    communities.submenu("home").register(
        "invenio_app_rdm_communities.communities_home",
        text=_("Home"),
        order=5,
        visible_when=_is_branded_community,
        expected_args=["pid_value"],
        icon="home",
        permissions="can_read",
    )
    communities.submenu("browse").register(
        endpoint="invenio_app_rdm_communities.communities_browse",
        text=_("Browse"),
        order=15,
        visible_when=_show_browse_page,
        expected_args=["pid_value"],
        icon="list",
        permissions="can_read",
    )
    communities.submenu("search").register(
        communities_detail_endpoint,
        text=_("Records"),
        order=10,
        expected_args=["pid_value"],
        icon="search",
        permissions=True,
    )
    communities.submenu("submit").register(
        "invenio_app_rdm_communities.community_static_page",
        text=_("Submit"),
        order=15,
        visible_when=_is_branded_community,
        endpoint_arguments_constructor=lambda: {
            "pid_value": (request.view_args or {}).get("pid_value"),
            "page_slug": "how-to-submit",
        },
        icon="upload",
        permissions="can_read",
    )


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    init_menu(app)
    ui_overrides(app)
