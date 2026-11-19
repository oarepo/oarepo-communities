# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Default configuration for oarepo-communities to be initialized at invenio_config.module entrypoint."""

from __future__ import annotations

from invenio_rdm_records.requests.subcommunities import RDMSubCommunityRequest

from oarepo_communities.requests.community_submission import CommunitySubmission

RDM_COMMUNITY_SUBMISSION_REQUEST_CLS = CommunitySubmission

# Use the RDM subcommunity request type (adds the self_html link that the
# request timeline UI needs); the bare invenio_communities class has links_item={}.
COMMUNITIES_SUB_REQUEST_CLS = RDMSubCommunityRequest

INVENIO_COLLECTIONS_COMMUNITY_SLUG = "global"
"""Slug of the community that holds cross-repository ("global") collection trees.

Set to ``None`` in deployment config to disable this behavior.
"""

RDM_COMMUNITY_COLLECTIONS_RECORDS_SERVICE_CLASS = (
    "oarepo_communities.collections.services:GlobalCollectionsRecordsService"
)
"""Collections records service that searches all records for the global community."""
