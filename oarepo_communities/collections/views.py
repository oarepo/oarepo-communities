#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI blueprint for the "global" collections pages.

Registers:

* ``/<prefix>``                                 — grid of every collection tree on the
                                                ``"global"`` holder community.
* ``/<prefix>/<tree_slug>/<collection_slug>``   — per-collection search page using
                                                the ``invenio-app-rdm-collections-search.js``
                                                bundle against the collection's records
                                                endpoint.

Also wires:
* per-endpoint UI overrides so the search page picks up the same result-list
  item / search-bar behavior as ``invenio_search_ui.search``.
* the top-level ``Collections`` main-menu item.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    render_template,
)
from flask_menu import current_menu
from invenio_collections.errors import LogoNotFoundError
from invenio_communities.communities.resources.serializer import UICommunityJSONSerializer
from invenio_communities.proxies import current_communities
from invenio_communities.views.communities import HEADER_PERMISSIONS
from invenio_i18n import lazy_gettext as _

if TYPE_CHECKING:
    from flask import Flask
    from flask.typing import ResponseReturnValue
    from invenio_communities.communities.records.api import Community


BLUEPRINT_NAME = "oarepo_communities_collections"
DEFAULT_URL_PREFIX = "/collections"
BROWSE_TEMPLATE = "oarepo_communities/collections/browse.html"
DETAIL_TEMPLATE = "oarepo_communities/collections/collection.html"


def create_blueprint(app: Flask) -> Blueprint:
    """Create the UI blueprint for the collections pages."""
    callbacks = app.config.setdefault("OAREPO_UI_RESULT_LIST_ITEM_REGISTRATION_CALLBACKS", [])
    if _register_collection_search_result_item not in callbacks:
        callbacks.append(_register_collection_search_result_item)

    blueprint = Blueprint(
        BLUEPRINT_NAME,
        __name__,
        url_prefix=app.config.get("INVENIO_COLLECTIONS_UI_URL_PREFIX", DEFAULT_URL_PREFIX),
        template_folder="templates",
    )
    blueprint.add_url_rule("", view_func=browse_collections)
    blueprint.add_url_rule("/<tree_slug>/<collection_slug>", view_func=collection_detail)
    return blueprint


def finalize_app(app: Flask) -> None:
    """UI-only finalize hook — registers overrides and the main-menu item.

    Registered under ``invenio_base.finalize_app`` (UI app only), not under
    ``invenio_base.api_finalize_app``, so it never runs on the API app where
    ``oarepo_ui`` is not installed as an extension.
    """
    ui_overrides(app)
    _init_menu(app)


def _init_menu(app: Flask) -> None:
    """Register the top-level ``Collections`` menu item, visible conditionally.

    The item is shown whenever ``COMMUNITIES_COLLECTIONS_ENABLED`` is truthy
    and ``INVENIO_COLLECTIONS_COMMUNITY_SLUG`` equals ``"global"``
    (see :func:`_collections_menu_visible`). Visibility is not gated on the
    holder community existing or having any collections; if those are missing
    the tab simply leads to an empty browse page.
    """
    with app.app_context():
        current_menu.submenu("main.collections").register(
            f"{BLUEPRINT_NAME}.browse_collections",
            _("Collections"),
            order=app.config.get("COMMUNITIES_COLLECTIONS_MENU_ORDER", 2),
            visible_when=_collections_menu_visible,
        )


def _collections_menu_visible() -> bool:
    """Return True if the Collections menu item should render.

    Requires ``COMMUNITIES_COLLECTIONS_ENABLED`` to be truthy and
    ``INVENIO_COLLECTIONS_COMMUNITY_SLUG`` to equal ``"global"``.
    """
    config = current_app.config
    return bool(
        config.get("COMMUNITIES_COLLECTIONS_ENABLED", False)
        and config.get("INVENIO_COLLECTIONS_COMMUNITY_SLUG") == "global"
    )


def ui_overrides(_app: Flask) -> None:
    """Register per-endpoint UI overrides for the collection detail page.

    ``oarepo_ui/templates/oarepo_ui/javascript.html`` auto-loads
    ``overrides-<request.endpoint>.js`` on every page — that bundle only
    exists if there is at least one ``UIComponentOverride`` registered for
    the endpoint. Registering the same overrides ``oarepo_ui`` uses for
    ``invenio_search_ui.search`` gives the collection detail page the same
    result rows / search bar behavior. Component names use the
    ``InvenioAppRDM.CollectionsSearch`` namespace because the template builds
    the search config with ``app_id="InvenioAppRDM.CollectionsSearch"``.
    """
    from oarepo_ui.overrides import UIComponent, UIComponentOverride
    from oarepo_ui.overrides.components import UIComponentImportMode
    from oarepo_ui.proxies import current_ui_overrides

    endpoint = f"{BLUEPRINT_NAME}.collection_detail"

    dynamic_result_list_item = UIComponentOverride(
        endpoint,
        "InvenioAppRDM.CollectionsSearch.ResultsList.item",
        UIComponent(
            "DynamicResultsListItem",
            "@js/oarepo_ui/search/DynamicResultsListItem",
            UIComponentImportMode.DEFAULT,
        ),
    )
    search_bar = UIComponentOverride(
        endpoint,
        "InvenioAppRDM.CollectionsSearch.SearchBar.element",
        UIComponent(
            "ClearableSearchbarElement",
            "@js/oarepo_ui/search/ClearableSearchbarElement",
            UIComponentImportMode.NAMED,
        ),
    )
    for override in (dynamic_result_list_item, search_bar):
        if override not in current_ui_overrides:
            current_ui_overrides.add(override)


def _register_collection_search_result_item(ui_overrides: Any, schema: str, component: Any) -> None:
    """Register a per-schema result item for the collection detail page.

    Mirrors ``oarepo_ui.views._register_main_search_result_item`` but targets
    the collection detail endpoint instead of ``invenio_search_ui.search``.
    Appended to ``OAREPO_UI_RESULT_LIST_ITEM_REGISTRATION_CALLBACKS`` from the
    blueprint factory so every call to
    ``current_oarepo_ui.register_result_list_item(schema, component)`` also
    registers the schema-specific override for this endpoint.
    """
    from oarepo_ui.overrides import UIComponentOverride

    override = UIComponentOverride(
        f"{BLUEPRINT_NAME}.collection_detail",
        f"InvenioAppRDM.CollectionsSearch.ResultsList.item.{schema}",
        component,
    )
    if override not in ui_overrides:
        ui_overrides.add(override)


def _resolve_collections_community() -> Community | None:
    """Return the community record acting as the collections namespace or None."""
    from invenio_communities.communities.records.api import Community
    from invenio_pidstore.errors import PIDDoesNotExistError

    slug = current_app.config.get("INVENIO_COLLECTIONS_COMMUNITY_SLUG")
    if not slug:
        return None
    try:
        return cast("Community", Community.pid.resolve(slug))
    except PIDDoesNotExistError:
        return None


def browse_collections() -> ResponseReturnValue:
    """Global collections browse page — grid of every tree on the holder community."""
    from invenio_rdm_records.proxies import (
        current_community_collections_service,  # pyright: ignore[reportAttributeAccessIssue]
    )

    community = _resolve_collections_community()
    trees: dict[int, dict[str, Any]] = {}
    if community is not None:
        trees = current_community_collections_service.list_trees(
            g.identity, namespace_id=community.id, depth=2
        ).to_dict()

    return render_template(
        current_app.config.get("OAREPO_COMMUNITIES_COLLECTIONS_BROWSE_TEMPLATE", BROWSE_TEMPLATE),
        trees=trees,
    )


def collection_detail(tree_slug: str, collection_slug: str) -> ResponseReturnValue:
    """Per-collection search page using the ``invenio-app-rdm-collections-search.js`` bundle.

    The search app queries ``/api/collections/<id>/records``, where the server
    layers the collection's saved ``search_query`` over whatever the user types.
    The template uses ``app_id="InvenioAppRDM.CollectionsSearch"``; result items
    and the search bar are wired by :func:`ui_overrides` and
    :func:`_register_collection_search_result_item`.
    """
    from invenio_collections.errors import CollectionNotFound, CollectionTreeNotFound
    from invenio_rdm_records.proxies import (
        current_community_collections_service,  # pyright: ignore[reportAttributeAccessIssue]
    )
    community = _resolve_collections_community()
    if community is None:
        return abort(404)

    g._menu_kwargs = {**(getattr(g, "_menu_kwargs", None) or {}), "pid_value": community.slug}

    community_result = current_communities.service.result_item(
        current_communities.service,
        identity=g.identity,
        record=community,
        links_tpl=current_communities.service.links_item_tpl,
        expandable_fields=current_communities.service.expandable_fields,
        nested_links_item=getattr(current_communities.service.config, "nested_links_item", None),
        expand=False,
    )

    community_ui = UICommunityJSONSerializer().dump_obj(community_result.to_dict())

    # An unknown tree_slug / collection_slug should render 404, not bubble up as 500.
    try:
        collection = current_community_collections_service.read(
            g.identity,
            slug=collection_slug,
            tree_slug=tree_slug,
            namespace_id=community.id,
        )

    except CollectionNotFound, CollectionTreeNotFound:
        abort(404)

    collection_ui = collection.to_dict()

    try:
        logo = current_community_collections_service.read_logo(g.identity, collection_slug)
    except LogoNotFoundError:
        logo = None

    return render_template(
        current_app.config.get("OAREPO_COMMUNITIES_COLLECTION_DETAIL_TEMPLATE", DETAIL_TEMPLATE),
        theme=community_ui.get("theme", {}),
        community=community_result,
        community_ui=community_ui,
        collection=collection_ui,
        tree=collection._collection.collection_tree,
        logo=logo,
        permissions=community_result.has_permissions_to(HEADER_PERMISSIONS),
    )
