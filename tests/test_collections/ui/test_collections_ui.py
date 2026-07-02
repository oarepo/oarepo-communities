#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Real UI tests for the collections blueprint.

Fires actual HTTP requests through the Flask test client at the UI app the
sibling ``conftest.py`` builds (it overrides the API factory used by the
service tests one level up).

Asserts real properties of the rendered pages:

* the browse grid actually lists the fixture collection and its card link
  points at the per-collection route;
* the detail page mounts the search app pointed at
  ``/api/collections/<id>/records`` (the whole point of the endpoint swap);
* the detail-page breadcrumb links back to ``/collections``;
* the ``main.collections`` menu item registered in ``finalize_app`` is
  visible when ``COMMUNITIES_COLLECTIONS_ENABLED`` is enabled and hidden
  when it is toggled off.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_menu import current_menu

if TYPE_CHECKING:
    from typing import Any

    from flask import Flask
    from flask.testing import FlaskClient


def test_browse_page_lists_the_collection(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """GET /collections renders the fixture tree + collection as a card."""
    resp = client.get("/collections")
    assert resp.status_code == 200, resp.data[:500].decode(errors="replace")
    body = resp.data.decode()
    assert "Test tree" in body
    assert "Test collection" in body
    assert "/collections/test-tree/test-collection" in body


def test_collection_detail_endpoint_targets_collection_records_api(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """The detail page mounts the search app at ``/api/collections/<id>/records``.

    That URL is what proves the endpoint swap in ``collection_detail`` fired
    — if the view falls back to the default ``/api/records``, this string
    would not appear anywhere in the rendered HTML.
    """
    resp = client.get("/collections/test-tree/test-collection")
    assert resp.status_code == 200, resp.data[:500].decode(errors="replace")
    body = resp.data.decode()
    collection_id = collection_with_query["id"]
    assert f"/api/collections/{collection_id}/records" in body, (
        f"Expected the search app to be pointed at "
        f"/api/collections/{collection_id}/records; if this fails, the "
        f"``endpoint`` argument in ``collection_detail`` regressed."
    )
    assert "data-invenio-search-config" in body


def test_collection_detail_breadcrumb_links_back_to_browse(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """The breadcrumb ``Collections`` link points back at the browse grid."""
    resp = client.get("/collections/test-tree/test-collection")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'href="/collections"' in body
    assert "Test collection" in body


def test_unknown_collection_returns_404(
    client: FlaskClient,
    collections_community,  # type: ignore[no-untyped-def]
) -> None:
    """A slug that does not resolve returns 404 through ``abort(404)``."""
    resp = client.get("/collections/no-such-tree/no-such-collection")
    assert resp.status_code == 404


def test_menu_item_is_visible_when_flag_enabled(
    app: Flask,
    collection_with_query: dict[str, Any],
) -> None:
    """Menu item is visible when ``COMMUNITIES_COLLECTIONS_ENABLED`` is truthy.

    Visibility is gated solely on the flag (see
    ``_collections_menu_visible``); it is not affected by whether the holder
    community exists or holds any collections.
    """
    with app.test_request_context("/"):
        item = current_menu.submenu("main.collections")
        assert item.visible is True, (
            "Expected the Collections menu item to be visible while COMMUNITIES_COLLECTIONS_ENABLED is enabled."
        )


def test_menu_item_is_hidden_when_flag_disabled(
    app: Flask,
    collection_with_query: dict[str, Any],
    set_app_config_fn_scoped,  # type: ignore[no-untyped-def]
) -> None:
    """Toggling ``COMMUNITIES_COLLECTIONS_ENABLED`` off hides the menu item."""
    set_app_config_fn_scoped({"COMMUNITIES_COLLECTIONS_ENABLED": False})
    with app.test_request_context("/"):
        item = current_menu.submenu("main.collections")
        assert item.visible is False
