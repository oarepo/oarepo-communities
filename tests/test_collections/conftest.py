#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Fixtures for the collections tests.

Everything real — no mocks. The top-level conftest already gives us the API
factory, the RDM records service, communities, workflows if we want them.
We only need to pin the config key our modified ``CommunityRecordsService``
reads and materialize a holder community, a "different" community, and a
tree + collection through the actual service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import (  # pyright: ignore[reportAttributeAccessIssue]
    current_community_collections_service,
)

if TYPE_CHECKING:
    from typing import Any

    from invenio_communities.communities.records.api import Community
    from pytest_invenio.user import UserFixtureBase
    from pytest_oarepo.communities.fixtures import (
        CommunityGetOrCreateFn,
        CommunityGetOrCreateWithoutWorkflowArgsFn,
    )


COLLECTIONS_COMMUNITY_SLUG = "collections-holder"
OTHER_COMMUNITY_SLUG = "some-other-community"
COLLECTION_QUERY = 'metadata.title:"collections-marker"'


@pytest.fixture(scope="module")
def extra_entry_points(communities_model):
    """Force ``communities_model.register()`` to run before ``entry_points``.

    ``entry_points`` (module scope, provided by pytest-invenio) feeds
    ``create_app``. Without this dependency edge, pytest is free to build
    the app before ``communities_model`` (session scope) has run —
    ``ModelImporter`` is not yet on ``sys.meta_path``, so the model's Flask
    extension entry point is invisible when the app scans entry points, and
    ``app.extensions[base_name]`` never gets set. The proxies at
    ``oarepo_model/presets/records_resources/proxy.py:55`` then blow up
    with ``KeyError: 'communities_test'`` the first time any test touches
    ``record_service`` / ``published_record_with_community_factory``. The
    empty dict below is fine — we only need the ordering constraint.
    """
    return {}


@pytest.fixture(scope="module")
def app_config(app_config: dict[str, Any]) -> dict[str, Any]:
    """Pin the config key the modified CommunityRecordsService reads."""
    app_config["INVENIO_COLLECTIONS_COMMUNITY_SLUG"] = COLLECTIONS_COMMUNITY_SLUG
    app_config["COMMUNITIES_COLLECTIONS_ENABLED"] = True
    return app_config


@pytest.fixture
def collections_community(
    community_get_or_create: CommunityGetOrCreateFn,
    community_owner: UserFixtureBase,
) -> Community:
    """Create (or resolve) the collections-holder community — no workflow needed."""
    return community_get_or_create(community_owner, slug=COLLECTIONS_COMMUNITY_SLUG)


@pytest.fixture
def other_community(
    community_get_or_create_in_default_workflow: CommunityGetOrCreateWithoutWorkflowArgsFn,
    community_owner: UserFixtureBase,
) -> Community:
    """Create a different community that will hold the actual test record.

    Needs the default workflow because ``published_record_with_community_factory``
    publishes through the community-workflow pipeline.
    """
    return community_get_or_create_in_default_workflow(community_owner, slug=OTHER_COMMUNITY_SLUG)


@pytest.fixture
def collection_with_query(collections_community: Community) -> dict[str, Any]:
    """Materialize a tree + collection on the collections-holder community.

    The collection's ``search_query`` is intentionally scoped by title so we
    can create a matching record in a *different* community and prove the
    community filter was skipped when the collections service resolves it.
    """
    current_community_collections_service.create_tree(
        system_identity,
        data={"title": "Test tree", "slug": "test-tree"},
        namespace_id=collections_community.id,
    )
    collection_item = current_community_collections_service.create(
        system_identity,
        data={
            "title": "Test collection",
            "slug": "test-collection",
            "search_query": COLLECTION_QUERY,
        },
        namespace_id=collections_community.id,
        tree_slug="test-tree",
    ).to_dict()
    return {
        "id": collection_item[collection_item["root"]]["id"],
        "wrapper": collection_item,
    }
