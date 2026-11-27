# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Real UI tests for the collections blueprint.

Fires actual HTTP requests through the Flask test client at the UI app the
sibling ``conftest.py`` builds (it overrides the API factory used by the
service tests one level up).

Asserts real properties of the rendered pages:

* the browse page lists the fixture tree and collection with a link to the
  collection's detail page, and shows an empty state when there are no trees;
* the detail page points its search app at the collection's
  ``/api/collections/<id>/records`` endpoint, and its breadcrumb links back
  to ``/collections``;
* an unknown tree or an unknown collection in an existing tree returns 404;
* the ``main.collections`` menu item registered in ``finalize_app`` links to
  the browse page; it is visible while the feature is enabled and hidden when
  ``COMMUNITIES_COLLECTIONS_ENABLED`` is off or ``COLLECTIONS_COMMUNITY_SLUG``
  is ``None``;
* with ``COLLECTIONS_COMMUNITY_SLUG = None`` the browse page renders empty and
  a collection detail page returns 404;
* a subcollection is listed under its parent on the browse page, and its
  detail page links to the parent in the breadcrumb and points its search app
  at the subcollection's ``/api/collections/<id>/records`` endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_menu import current_menu

from ..constants import (
    COLLECTION_SLUG,
    COLLECTION_TITLE,
    SUBCOLLECTION_SLUG,
    SUBCOLLECTION_TITLE,
    TREE_SLUG,
    TREE_TITLE,
)

if TYPE_CHECKING:
    from typing import Any

    from flask import Flask
    from flask.testing import FlaskClient
    from invenio_communities.communities.records.api import Community


def test_browse_page_lists_the_collection(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """GET /collections renders the fixture tree + collection."""
    resp = client.get("/collections")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert TREE_TITLE in body
    assert COLLECTION_TITLE in body
    assert f'href="/collections/{TREE_SLUG}/{COLLECTION_SLUG}"' in body, "The collection must link to its detail page."


def test_collection_detail_search_app_targets_collection_records_api(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """The detail page points its search app at the collection's records endpoint.

    The template passes the collection's ``links.search`` to the search app
    config, so the page searches through ``/api/collections/<id>/records``
    (and thus applies the collection's query) instead of a generic records
    endpoint.
    """
    resp = client.get(f"/collections/{TREE_SLUG}/{COLLECTION_SLUG}")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "data-invenio-search-config" in body, "The detail page must render the search app."

    collection_id = collection_with_query["id"]
    assert f"/api/collections/{collection_id}/records" in body, (
        f"The search app must query /api/collections/{collection_id}/records — "
        "check the collection's ``links.search`` and the template's "
        "``search_app_collection_config`` call."
    )


def test_collection_detail_breadcrumb_links_back_to_browse(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """The breadcrumb starts with a link to the browse page and ends with the collection.

    The ``class="section"`` markup is specific to the breadcrumb; the main
    menu also links to ``/collections``, so a plain ``href`` check would pass
    even without a breadcrumb.
    """
    resp = client.get(f"/collections/{TREE_SLUG}/{COLLECTION_SLUG}")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert '<a class="section" href="/collections">' in body, (
        "The breadcrumb must start with a link back to the browse page."
    )
    assert f'<span class="section active">{COLLECTION_TITLE}</span>' in body, (
        "The breadcrumb must end with the current collection as the active item."
    )


def test_unknown_tree_returns_404(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """An unknown tree returns 404 even when the collection slug exists elsewhere.

    ``CollectionTree.resolve`` raises ``CollectionTreeNotFound``, which
    ``collection_detail`` turns into ``abort(404)``.
    """
    resp = client.get(f"/collections/no-such-tree/{COLLECTION_SLUG}")
    assert resp.status_code == 404


def test_unknown_collection_in_existing_tree_returns_404(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
) -> None:
    """An unknown collection in an existing tree returns 404.

    ``Collection.read`` raises ``CollectionNotFound``, which
    ``collection_detail`` turns into ``abort(404)``.
    """
    resp = client.get(f"/collections/{TREE_SLUG}/no-such-collection")
    assert resp.status_code == 404


def test_menu_item_is_visible_when_flag_enabled(app: Flask) -> None:
    """The Collections menu item is registered, links to the browse page and is visible.

    ``_collections_menu_visible`` requires ``COMMUNITIES_COLLECTIONS_ENABLED``
    to be truthy and ``COLLECTIONS_COMMUNITY_SLUG`` to equal ``"global"``.
    It does not check whether the community exists or holds any collections.
    """
    with app.test_request_context("/"):
        item = current_menu.submenu("main.collections")
        assert item.url == "/collections"
        assert item.visible is True


def test_menu_item_is_hidden_when_flag_disabled(
    app: Flask,
    set_app_config_fn_scoped,
) -> None:
    """Turning ``COMMUNITIES_COLLECTIONS_ENABLED`` off hides the registered menu item."""
    set_app_config_fn_scoped({"COMMUNITIES_COLLECTIONS_ENABLED": False})
    with app.test_request_context("/"):
        item = current_menu.submenu("main.collections")
        # the item stays registered; only the flag hides it
        assert item.url == "/collections"
        assert item.visible is False


def test_menu_item_is_hidden_when_collections_community_slug_is_none(
    app: Flask,
    set_app_config_fn_scoped,
) -> None:
    """With ``COLLECTIONS_COMMUNITY_SLUG = None`` the feature is off, so the menu item is hidden."""
    set_app_config_fn_scoped({"COLLECTIONS_COMMUNITY_SLUG": None})
    with app.test_request_context("/"):
        item = current_menu.submenu("main.collections")
        assert item.url == "/collections"
        assert item.visible is False


def test_pages_are_empty_when_collections_community_slug_is_none(
    client: FlaskClient,
    collection_with_query: dict[str, Any],
    set_app_config_fn_scoped,
) -> None:
    """With ``COLLECTIONS_COMMUNITY_SLUG = None`` the collections UI serves nothing.

    The browse page renders empty and a collection detail page returns 404.
    """
    set_app_config_fn_scoped({"COLLECTIONS_COMMUNITY_SLUG": None})

    resp = client.get("/collections")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "No collections available." in body
    assert COLLECTION_TITLE not in body

    resp = client.get(f"/collections/{TREE_SLUG}/{COLLECTION_SLUG}")
    assert resp.status_code == 404


def test_browse_page_without_collections_shows_empty_state(
    client: FlaskClient,
    collections_community: Community,
) -> None:
    """The browse page renders an empty state when the community has no trees."""
    resp = client.get("/collections")
    assert resp.status_code == 200
    assert "No collections available." in resp.data.decode()


def test_browse_page_lists_the_subcollection(
    client: FlaskClient,
    subcollection: dict[str, Any],
) -> None:
    """The browse page lists a subcollection under its parent with a link to its detail."""
    resp = client.get("/collections")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert SUBCOLLECTION_TITLE in body
    # the template quotes child links with single quotes
    assert f"href='/collections/{TREE_SLUG}/{SUBCOLLECTION_SLUG}'" in body, (
        "The subcollection must link to its detail page."
    )


def test_subcollection_detail_breadcrumb_and_search_app(
    client: FlaskClient,
    subcollection: dict[str, Any],
) -> None:
    """The subcollection detail links back to its parent and searches the subcollection.

    ``breadcrumbs`` lists the ancestors followed by the collection itself, so
    the parent is rendered as a link and the subcollection as the active item.
    """
    resp = client.get(f"/collections/{TREE_SLUG}/{SUBCOLLECTION_SLUG}")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert f'<a class="section" href="/collections/{TREE_SLUG}/{COLLECTION_SLUG}">' in body, (
        "The breadcrumb must link to the parent collection."
    )
    assert f'<span class="section active">{SUBCOLLECTION_TITLE}</span>' in body
    assert f"/api/collections/{subcollection['id']}/records" in body, (
        "The search app must query the subcollection, not its parent."
    )
