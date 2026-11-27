# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Shared constants for the collections tests.

Kept out of ``conftest.py`` so test modules can import them directly.
The search queries are built from the marker values, so a record's data
and the query that should match it can never drift apart.
"""

from __future__ import annotations

COLLECTIONS_COMMUNITY_SLUG = "global"
OTHER_COMMUNITY_SLUG = "some-other-community"
THIRD_COMMUNITY_SLUG = "third-community"
RESTRICTED_COMMUNITY_SLUG = "restricted-community"

TREE_SLUG = "test-tree"
COLLECTION_SLUG = "test-collection"
SUBCOLLECTION_SLUG = "test-subcollection"

TREE_TITLE = "Test tree"
COLLECTION_TITLE = "Test collection"
SUBCOLLECTION_TITLE = "Test subcollection"

COLLECTION_MARKER_TITLE = "collections-marker"
SUBCOLLECTION_CONTRIBUTOR = "Contributor 1"

COLLECTION_QUERY = f'metadata.title:"{COLLECTION_MARKER_TITLE}"'
SUBCOLLECTION_QUERY = f'metadata.contributors:"{SUBCOLLECTION_CONTRIBUTOR}"'
