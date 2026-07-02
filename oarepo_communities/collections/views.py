#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI blueprint for the "global" collections pages.

Registers:

* ``/<prefix>``                          — grid of every collection tree on the
                                           configured "collections" community.
* ``/<prefix>/<tree_slug>/<col_slug>``   — per-collection search page reusing
                                           the main ``invenio-app-rdm-search.js``
                                           bundle with the ``searchApi`` URL
                                           swapped to the collection's records
                                           endpoint.

Also wires:

* an app-template global ``collection_logo_url`` mirroring upstream's
  ``read_logo`` static-file convention, and
* per-endpoint UI overrides so the search page picks up the same result-list
  item / search-bar behavior as ``invenio_search_ui.search``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import (
    Blueprint,
    current_app,
    g,
    render_template,
)
from flask_menu import current_menu
from invenio_access.permissions import system_identity
from invenio_i18n import lazy_gettext as _

if TYPE_CHECKING:
    from flask import Flask
    from flask.typing import ResponseReturnValue


BLUEPRINT_NAME = "oarepo_communities_collections"
DEFAULT_URL_PREFIX = "/collections"
BROWSE_TEMPLATE = "oarepo_communities/collections/browse.html"
DETAIL_TEMPLATE = "oarepo_communities/collections/collection.html"


def create_blueprint(app: Flask) -> Blueprint:
    """Create the UI blueprint for the collections pages."""
    from invenio_collections.errors import CollectionNotFound, CollectionTreeNotFound

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
    blueprint.add_url_rule("/<tree_slug>/<col_slug>", view_func=collection_detail)
    # An unknown tree_slug / col_slug should render 404, not bubble up as 500.
    blueprint.register_error_handler(CollectionNotFound, _collection_not_found)
    blueprint.register_error_handler(CollectionTreeNotFound, _collection_not_found)
    return blueprint


def _collection_not_found(_error: Exception) -> ResponseReturnValue:
    """Convert missing tree/collection errors from the service into a 404.

    Returns a response tuple rather than calling ``abort(404)`` because
    ``PROPAGATE_EXCEPTIONS`` is on in tests — ``abort`` would raise
    ``NotFound`` through the test client instead of yielding a 404 response.
    """
    return "Collection not found", 404


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

    Hidden unless every gate below passes at request-render time:

    1. ``COMMUNITIES_COLLECTIONS_ENABLED`` is truthy (defaults to True upstream).
    2. ``INVENIO_COLLECTIONS_COMMUNITY_SLUG`` resolves to a real community.
    3. That community actually has at least one collection.

    Uses ``system_identity`` for the visibility probe so anonymous visitors
    still see the menu item when public collections exist.
    """
    with app.app_context():
        current_menu.submenu("main.collections").register(
            f"{BLUEPRINT_NAME}.browse_collections",
            _("Collections"),
            order=app.config.get("COMMUNITIES_COLLECTIONS_MENU_ORDER", 2),
            visible_when=_collections_menu_visible,
        )


def _collections_menu_visible() -> bool:
    """Return True if the Collections menu item should render."""
    from invenio_rdm_records.proxies import (
        current_community_collections_service,  # pyright: ignore[reportAttributeAccessIssue]
    )

    if not current_app.config.get("COMMUNITIES_COLLECTIONS_ENABLED", True):
        return False
    community = _resolve_collections_community()
    if community is None:
        return False
    try:
        trees = current_community_collections_service.list_trees(
            system_identity, namespace_id=community.id, depth=1
        ).to_dict()
    except Exception:  # noqa: BLE001
        return False
    return any(bool(tree.get("collections")) for tree in trees.values())


def ui_overrides(_app: Flask) -> None:
    """Register per-endpoint UI overrides for the collection detail page.

    ``oarepo_ui/templates/oarepo_ui/javascript.html`` auto-loads
    ``overrides-<request.endpoint>.js`` on every page — that bundle only
    exists if there is at least one ``UIComponentOverride`` registered for
    the endpoint. Registering the same overrides ``oarepo_ui`` uses for
    ``invenio_search_ui.search`` gives the collection detail page the same
    result rows / search bar behavior. Component names use the
    ``InvenioAppRdm.Search`` namespace because the view builds the search
    config with ``app_id="InvenioAppRdm.Search"`` — identical to ``/search``.
    """
    from oarepo_ui.overrides import UIComponent, UIComponentOverride
    from oarepo_ui.overrides.components import UIComponentImportMode
    from oarepo_ui.proxies import current_ui_overrides

    endpoint = f"{BLUEPRINT_NAME}.collection_detail"

    dynamic_result_list_item = UIComponentOverride(
        endpoint,
        "InvenioAppRdm.Search.ResultsList.item",
        UIComponent(
            "DynamicResultsListItem",
            "@js/oarepo_ui/search/DynamicResultsListItem",
            UIComponentImportMode.DEFAULT,
        ),
    )
    search_bar = UIComponentOverride(
        endpoint,
        "InvenioAppRdm.Search.SearchBar.element",
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
        f"InvenioAppRdm.Search.ResultsList.item.{schema}",
        component,
    )
    if override not in ui_overrides:
        ui_overrides.add(override)


def _resolve_collections_community() -> Any:
    """Return the community record acting as the collections namespace or None."""
    from invenio_communities.proxies import current_communities
    from invenio_pidstore.errors import PIDDoesNotExistError

    slug = current_app.config.get("INVENIO_COLLECTIONS_COMMUNITY_SLUG")
    if not slug:
        return None
    try:
        return current_communities.service.record_cls.pid.resolve(slug)
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


def collection_detail(tree_slug: str, col_slug: str) -> ResponseReturnValue:
    """Per-collection search page reusing the main ``invenio-app-rdm-search.js`` bundle.

    ``searchApi.axios.url`` is swapped to ``/api/collections/<id>/records``,
    where the server layers the collection's saved ``search_query`` over
    whatever the user types. ``app_id="InvenioAppRdm.Search"`` matches
    ``/search``, so every override registered against that endpoint (via
    our own ``ui_overrides``) applies without any additional wiring.
    """
    from invenio_rdm_records.proxies import (
        current_community_collections_service,  # pyright: ignore[reportAttributeAccessIssue]
    )
    from invenio_search_ui.searchconfig import (
        search_app_config as build_search_app_config,
    )

    community = _resolve_collections_community()
    if community is None:
        return "Collection not found", 404

    collection = current_community_collections_service.read(
        g.identity,
        slug=col_slug,
        tree_slug=tree_slug,
        namespace_id=community.id,
    ).to_dict()

    root_collection = collection[collection["root"]]
    endpoint_url = root_collection["links"]["search"]
    search_app_config = build_search_app_config(
        config_name="RDM_SEARCH",
        available_facets=current_app.config["RDM_FACETS"],
        sort_options=current_app.config["RDM_SORT_OPTIONS"],
        endpoint=endpoint_url,
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
        app_id="InvenioAppRdm.Search",
        pagination_options=(10, 20),
    )

    return render_template(
        current_app.config.get("OAREPO_COMMUNITIES_COLLECTION_DETAIL_TEMPLATE", DETAIL_TEMPLATE),
        community=community,
        collection=collection,
        tree_slug=tree_slug,
        search_app_config=search_app_config,
    )
