#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Real-integration tests for the collections community-filter skip.

The whole point of ``INVENIO_COLLECTIONS_COMMUNITY_SLUG`` is that when a
tree/collection sits on that community and its records endpoint is queried,
the community filter is dropped so a collection's ``search_query`` resolves
against every published record — not only records tagged with the holder.

These tests publish a real record into a *different* community, then hit the
collection's records endpoint and assert the record comes back. Success means
the community filter was skipped; the skip is implemented by the collections
records service in oarepo-rdm.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import (  # pyright: ignore[reportAttributeAccessIssue]
    current_community_collections_service,
)

if TYPE_CHECKING:
    from typing import Any

    from invenio_communities.communities.records.api import Community
    from pytest_oarepo.communities.records import CreateCommunityRecordFn


def test_collection_search_returns_records_from_other_communities(
    app,  # type: ignore[no-untyped-def]
    communities_model,  # type: ignore[no-untyped-def]
    community_owner,  # type: ignore[no-untyped-def]
    other_community: Community,
    collection_with_query: dict[str, Any],
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,  # type: ignore[no-untyped-def]
) -> None:
    """Records live in another community; the collection still finds them.

    Setup:
      * ``collection_with_query`` = tree + collection on the holder community
        with ``search_query = 'metadata.title:"collections-marker"'``.
      * We publish a record with that exact title into ``other_community``
        (definitely not the holder).

    Expectation:
      * Searching the collection's records endpoint returns that record.
      * A control record without the marker title in the same other-community
        is *not* returned — proving the collection's saved query is still the
        gate, not just "return everything cross-community".
    """
    matching = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": "collections-marker"}},
    )
    control = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": "should-not-match"}},
    )

    communities_model.Record.index.refresh()

    results = current_community_collections_service.search_collection_records(
        system_identity, collection_with_query["id"]
    ).to_dict()

    hit_ids = {hit["id"] for hit in results["hits"]["hits"]}
    assert matching["id"] in hit_ids, (
        "The cross-community record matching the collection query must be "
        "returned — this is exactly what the community-filter skip enables."
    )
    assert control["id"] not in hit_ids, (
        "The collection's own search_query must still gate results; a record "
        "that doesn't match the title query must be excluded."
    )


def test_search_without_the_collections_community_still_filters_by_community(
    app,  # type: ignore[no-untyped-def]
    communities_model,  # type: ignore[no-untyped-def]
    community_owner,  # type: ignore[no-untyped-def]
    other_community: Community,
    community_get_or_create_in_default_workflow,  # type: ignore[no-untyped-def]
    published_record_with_community_factory: CreateCommunityRecordFn,
    search_clear,  # type: ignore[no-untyped-def]
) -> None:
    """Negative control: the skip must be scoped to the collections community.

    A different community should still filter by its own
    ``parent.communities.ids`` — otherwise the change would leak
    cross-community results everywhere.
    """
    third_community = community_get_or_create_in_default_workflow(community_owner, slug="third-community")

    in_third = published_record_with_community_factory(
        community_owner.identity,
        str(third_community.id),
        additional_data={"metadata": {"title": "only-in-third"}},
    )
    in_other = published_record_with_community_factory(
        community_owner.identity,
        str(other_community.id),
        additional_data={"metadata": {"title": "only-in-other"}},
    )

    communities_model.Record.index.refresh()

    records_service = current_community_collections_service.records_service
    results = records_service.search(system_identity, community_id=str(third_community.id)).to_dict()
    hit_ids = {hit["id"] for hit in results["hits"]["hits"]}

    assert in_third["id"] in hit_ids
    assert in_other["id"] not in hit_ids, (
        "Filtering by a non-collections community must still restrict to that "
        "community's records — the skip only fires for the configured slug."
    )
