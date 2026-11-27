# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Real-integration tests for the collections community-filter skip.

The whole point of ``COLLECTIONS_COMMUNITY_SLUG`` is that searching a
collection whose tree belongs to that community drops the community filter,
so the collection's ``search_query`` resolves against every published record,
not only records in that community.

These tests cover:

* **inside the configured community**: records are published into a
  *different* community, yet a collection on the ``COLLECTIONS_COMMUNITY_SLUG``
  community still returns them, because the community filter was skipped;
  a subcollection there ANDs its query with the parent's across communities;
* **any other community**: a collection on it still returns only its own
  community's records matching its query, so the skip does not leak elsewhere;
* **feature disabled**: with ``COLLECTIONS_COMMUNITY_SLUG = None`` the
  configured community behaves like any other and is filtered by community;
* **permissions**: the cross-community search still applies the caller's
  read permissions, so an anonymous user does not see restricted records.

The skip is implemented by ``GlobalCollectionsRecordsService`` in
``oarepo_communities.collections.services``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_principal import AnonymousIdentity
from invenio_access.permissions import any_user, system_identity
from invenio_rdm_records.proxies import (
    current_community_collections_service,
)

from .constants import (
    COLLECTION_MARKER_TITLE,
    SUBCOLLECTION_CONTRIBUTOR,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from flask_principal import Identity
    from invenio_communities.communities.records.api import Community
    from invenio_records_resources.services.records.results import RecordList
    from pytest_oarepo.communities.records import CreateCommunityRecordFn


def _hit_ids(result: RecordList) -> set[str]:
    """Return the ids of all hits in a search result."""
    return {hit["id"] for hit in result.to_dict()["hits"]["hits"]}


def test_collection_search_returns_records_from_other_communities(
    app,
    communities_model,
    community_owner,
    other_community: Community,
    collection_with_query: dict[str, Any],
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,
) -> None:
    """Records live in another community; the collection still finds them.

    Setup:
      * ``collection_with_query`` = tree + collection on the ``global`` community
        with ``COLLECTION_QUERY``, which matches the title
        ``COLLECTION_MARKER_TITLE``.
      * We publish a record with that title into ``other_community``
        (not the ``global`` community).

    Expectations:
      * Searching the collection returns that record.
      * A control record without the marker title in the same other-community
        is *not* returned — proving the collection's saved query is still the
        gate, not just "return everything cross-community".
    """
    matching = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )
    control = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": "should-not-match"}},
    )

    communities_model.Record.index.refresh()

    hit_ids = _hit_ids(
        current_community_collections_service.search_collection_records(system_identity, collection_with_query["id"])
    )

    assert matching["id"] in hit_ids, (
        "The cross-community record matching the collection query must be "
        "returned — this is exactly what the community-filter skip enables."
    )
    assert control["id"] not in hit_ids, (
        "The collection's own search_query must still gate results; a record "
        "that doesn't match the title query must be excluded."
    )


def test_collection_on_regular_community_filters_by_community_and_query(
    app,
    communities_model,
    community_owner,
    other_community: Community,
    third_community: Community,
    collection_factory: Callable[..., dict[str, Any]],
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,
) -> None:
    """Negative control: the filter skip must be scoped to the collections community.

    Setup:
      * the same tree + collection as ``collection_with_query``, but on
        ``other_community`` instead of the ``global`` community.

    Expectations:
      * A matching record in the collection's own community is returned.
      * A matching record in a different community is excluded — the
        community filter still applies outside the configured slug.
      * A non-matching record in the collection's own community is excluded —
        the collection's search_query still applies on this code path too.
    """
    collection = collection_factory(other_community.id)

    in_own_community = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )
    in_third_community = published_record_with_community_factory(
        community_owner.identity,
        str(third_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )
    control = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": "should-not-match"}},
    )

    communities_model.Record.index.refresh()

    hit_ids = _hit_ids(
        current_community_collections_service.search_collection_records(system_identity, collection["id"])
    )

    assert in_own_community["id"] in hit_ids, (
        "A record in the collection's own community matching its query must be returned."
    )
    assert in_third_community["id"] not in hit_ids, (
        "A matching record from another community must be excluded — the filter "
        "skip only applies to the configured collections community."
    )
    assert control["id"] not in hit_ids, (
        "A non-matching record must be excluded — the collection's search_query "
        "must still apply on a regular community."
    )


def test_subcollection_search_combines_parent_and_child_queries(
    app,
    communities_model,
    community_owner,
    other_community: Community,
    subcollection: dict[str, Any],
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,
) -> None:
    """A subcollection ANDs its query with the parent's, across communities.

    Setup:
      * ``collection_with_query`` (parent) uses ``COLLECTION_QUERY``
        (title ``COLLECTION_MARKER_TITLE``).
      * ``subcollection`` uses ``SUBCOLLECTION_QUERY``
        (contributor ``SUBCOLLECTION_CONTRIBUTOR``).
      * All records are published into ``other_community``, not ``global``.

    Expectations:
      * A record matching both queries is returned (cross-community works).
      * A record matching only the parent query is excluded.
      * A record matching only the subcollection query is excluded.
    """

    def record_data(title: str, contributors: list[str]) -> dict[str, Any]:
        # custom_data replaces the defaults entirely. additional_data would
        # append to the factory's default contributors (["Contributor 1"],
        # the same as SUBCOLLECTION_CONTRIBUTOR), so every record would match
        # the subcollection query.
        return {
            "metadata": {
                "title": title,
                "creators": ["Creator 1"],
                "contributors": contributors,
            },
            "files": {"enabled": False},
        }

    in_both = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        custom_data=record_data(COLLECTION_MARKER_TITLE, [SUBCOLLECTION_CONTRIBUTOR]),
    )
    only_parent = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        custom_data=record_data(COLLECTION_MARKER_TITLE, ["Contributor 55"]),
    )
    only_sub = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        custom_data=record_data("should-not-match", [SUBCOLLECTION_CONTRIBUTOR]),
    )

    communities_model.Record.index.refresh()

    hit_ids = _hit_ids(
        current_community_collections_service.search_collection_records(system_identity, subcollection["id"])
    )

    assert in_both["id"] in hit_ids, (
        "A cross-community record matching both the parent and the subcollection query must be returned."
    )
    assert only_parent["id"] not in hit_ids, (
        "A record matching only the parent query must be excluded — the subcollection's own search_query must apply."
    )
    assert only_sub["id"] not in hit_ids, (
        "A record matching only the subcollection query must be excluded — the parent's search_query must be ANDed in."
    )


def test_collections_community_slug_none_disables_filter_skip(
    app,
    communities_model,
    community_owner,
    other_community: Community,
    collection_with_query: dict[str, Any],
    published_record_with_community_factory: CreateCommunityRecordFn,
    set_app_config_fn_scoped,
    search_clear,
) -> None:
    """Setting ``COLLECTIONS_COMMUNITY_SLUG`` to ``None`` turns the skip off.

    Setup:
      * ``collection_with_query`` = tree + collection on the ``global`` community.
      * A record matching the collection query is published into
        ``other_community``.

    Expectations:
      * With the slug configured, the collection returns the record (sanity
        check — the same search the other tests rely on).
      * With the slug set to ``None``, the same collection filters by its own
        community like any other, so the record is excluded.
    """
    matching = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )

    communities_model.Record.index.refresh()

    def search() -> set[str]:
        return _hit_ids(
            current_community_collections_service.search_collection_records(
                system_identity, collection_with_query["id"]
            )
        )

    assert matching["id"] in search(), (
        "With COLLECTIONS_COMMUNITY_SLUG configured, the collection on the global "
        "community must return the cross-community record."
    )

    set_app_config_fn_scoped({"COLLECTIONS_COMMUNITY_SLUG": None})

    assert matching["id"] not in search(), (
        "With COLLECTIONS_COMMUNITY_SLUG set to None, no community holds global "
        "collections, so the collection must filter by its own community."
    )


def test_collection_search_respects_read_permissions(
    app,
    communities_model,
    community_owner,
    other_community: Community,
    restricted_community: Community,
    collection_with_query: dict[str, Any],
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,
) -> None:
    """The cross-community search still applies the caller's read permissions.

    Setup:
      * ``collection_with_query`` = tree + collection on the ``global`` community.
      * A matching record published into ``other_community`` (public workflow).
      * A matching record published into ``restricted_community``, whose
        workflow lets only record owners and community owners read it.

    Expectations:
      * The community owner sees both records — the restricted one really is
        part of the collection, so its absence below is due to permissions.
      * An anonymous user sees only the public record.
    """
    public = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )
    restricted = published_record_with_community_factory(
        community_owner.identity,
        str(restricted_community.id),
        additional_data={"metadata": {"title": COLLECTION_MARKER_TITLE}},
    )

    communities_model.Record.index.refresh()

    def search(identity: Identity) -> set[str]:
        return _hit_ids(
            current_community_collections_service.search_collection_records(identity, collection_with_query["id"])
        )

    owner_hits = search(community_owner.identity)
    assert public["id"] in owner_hits, "The owner must see the public cross-community record."
    assert restricted["id"] in owner_hits, (
        "The owner must see the restricted record — otherwise the anonymous check below proves nothing."
    )

    anonymous = AnonymousIdentity()
    anonymous.provides.add(any_user)
    anonymous_hits = search(anonymous)
    assert public["id"] in anonymous_hits, "An anonymous user must see the public cross-community record."
    assert restricted["id"] not in anonymous_hits, (
        "An anonymous user must not see a restricted record — the global search must not bypass read permissions."
    )
