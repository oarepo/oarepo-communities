# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Fixtures for the collections tests.

Everything real — no mocks. The top-level conftest already provides the API
factory, the RDM records service, communities and workflows. Here we enable
collections in the app config (``COMMUNITIES_COLLECTIONS_ENABLED``,
``COLLECTIONS_COMMUNITY_SLUG`` and limits) and create, through the real
services:

* the ``global`` community that holds the collection trees;
* other communities for the test records (``other_community``,
  ``third_community``, and ``restricted_community`` with a non-public workflow);
* a tree + collection on any community (``collection_factory``), on the
  ``global`` community (``collection_with_query``) and a subcollection under it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import (
    current_community_collections_service,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from invenio_communities.communities.records.api import Community
    from pytest_invenio.user import UserFixtureBase
    from pytest_oarepo.communities.fixtures import (
        CommunityGetOrCreateFn,
        CommunityGetOrCreateWithoutWorkflowArgsFn,
    )

from .constants import (
    COLLECTION_QUERY,
    COLLECTION_SLUG,
    COLLECTION_TITLE,
    COLLECTIONS_COMMUNITY_SLUG,
    OTHER_COMMUNITY_SLUG,
    RESTRICTED_COMMUNITY_SLUG,
    SUBCOLLECTION_QUERY,
    SUBCOLLECTION_SLUG,
    SUBCOLLECTION_TITLE,
    THIRD_COMMUNITY_SLUG,
    TREE_SLUG,
    TREE_TITLE,
)


@pytest.fixture(scope="module")
def app_config(app_config: dict[str, Any]) -> dict[str, Any]:
    """Configure collections for tests: enable the feature, pin the slug and limits."""
    app_config["COLLECTIONS_COMMUNITY_SLUG"] = COLLECTIONS_COMMUNITY_SLUG
    app_config["COMMUNITIES_COLLECTIONS_ENABLED"] = True
    app_config["COLLECTIONS_MAX_DEPTH"] = 1
    app_config["COLLECTIONS_MAX_TREES"] = 10
    app_config["COLLECTIONS_MAX_COLLECTIONS_PER_TREE"] = 100

    return app_config


@pytest.fixture
def collections_community(
    community_get_or_create: CommunityGetOrCreateFn,
    community_owner: UserFixtureBase,
) -> Community:
    """Create (or resolve) the ``global`` community that holds collection trees."""
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
def third_community(
    community_get_or_create_in_default_workflow: CommunityGetOrCreateWithoutWorkflowArgsFn,
    community_owner: UserFixtureBase,
) -> Community:
    """Create a community whose records must stay out of another community's collection."""
    return community_get_or_create_in_default_workflow(community_owner, slug=THIRD_COMMUNITY_SLUG)


@pytest.fixture
def restricted_community(
    community_get_or_create: CommunityGetOrCreateFn,
    community_owner: UserFixtureBase,
) -> Community:
    """Create a community whose published records are readable only by owners."""
    return community_get_or_create(
        community_owner,
        slug=RESTRICTED_COMMUNITY_SLUG,
        workflow="restricted_read",
        allowed_workflows=["restricted_read"],
    )


@pytest.fixture
def collection_factory() -> Callable[..., dict[str, Any]]:
    """Return a function creating a tree + collection on the given community.

    The collection's ``search_query`` matches records by title, so a test can
    publish matching records into other communities and check whether the
    community filter was applied or skipped.
    """

    def _create(namespace_id: Any) -> dict[str, Any]:
        # section (= CollectionTree): titled container for collections
        current_community_collections_service.create_tree(
            system_identity,
            data={
                "title": TREE_TITLE,
                "slug": TREE_SLUG,
            },
            namespace_id=namespace_id,
        )
        # collection inside section
        collection_item = current_community_collections_service.create(
            system_identity,
            data={
                "title": COLLECTION_TITLE,
                "slug": COLLECTION_SLUG,
                "search_query": COLLECTION_QUERY,
            },
            namespace_id=namespace_id,
            tree_slug=TREE_SLUG,
        ).to_dict()
        return {
            "id": collection_item[collection_item["root"]]["id"],
            "wrapper": collection_item,
        }

    return _create


@pytest.fixture
def collection_with_query(
    collections_community: Community,
    collection_factory: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Create a tree + collection on the ``global`` community."""
    return collection_factory(collections_community.id)


@pytest.fixture
def subcollection(
    collections_community: Community,
    collection_with_query: dict[str, Any],
) -> dict[str, Any]:
    """Create a subcollection under ``test-collection``."""
    item = current_community_collections_service.add(
        system_identity,
        slug=COLLECTION_SLUG,
        data={
            "title": SUBCOLLECTION_TITLE,
            "slug": SUBCOLLECTION_SLUG,
            "search_query": SUBCOLLECTION_QUERY,
        },
        namespace_id=collections_community.id,
        tree_slug=TREE_SLUG,
    ).to_dict()
    return {
        "id": item[item["root"]]["id"],
        "wrapper": item,
    }
