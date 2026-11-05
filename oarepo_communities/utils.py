# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Utility functions for communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_communities.communities.records.api import Community

if TYPE_CHECKING:
    from invenio_drafts_resources.records import Record as RecordWithParent


def community_id_from_record(record: RecordWithParent) -> str | None:
    """Get community ID from record or its parent community."""
    community_id: str
    if isinstance(record, Community):
        community_id = str(record.id)
    else:
        parent_record: Any = record.parent if hasattr(record, "parent") else record
        try:
            community_id = str(parent_record.communities.default.id)
        except AttributeError:
            return None
    return community_id


def community_to_dict(community: Community) -> dict:
    """Convert community to dict suitable for embedding in record metadata."""
    return {
        "slug": str(community.slug),
        "id": str(community.id),
        "logo": f"/api/communities/{community.id}/logo",
        "links": {
            "self_html": f"/communities/{community.id}/records",
        },
        **(community.metadata or {}),
    }


def get_default_community_id_from_record(record: RecordWithParent) -> str:
    """Retrieve the default community ID from the given record.

    This function attempts to extract the default community ID associated with the
    parent of the provided record. If it isn't present, it looks at the review associated with the record.
    """
    if record.parent.communities.default:
        return str(record.parent.communities.default.id)
    return str(record.parent.review.receiver._parse_ref_dict_id())  # noqa SLF001


def get_community_ids_from_record(record: RecordWithParent) -> list[str]:
    """Extract the list of community IDs associated with a given record.

    This function attempts to extract the community IDs associated with the
    parent of the provided record. If it isn't present, it looks at the review associated with the record.
    """
    communities = record.parent.communities.ids
    if not communities:
        return [str(record.parent.review.receiver._parse_ref_dict_id())]  # noqa SLF001
    return list(communities)
