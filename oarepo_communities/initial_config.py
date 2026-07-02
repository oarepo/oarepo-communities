#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
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

Collections on this community search across every published record instead of
only records tagged with the holder community (the ``parent.communities.ids``
filter is skipped). The behavior is implemented by the collections records
service in oarepo-rdm. Set to ``None`` in deployment config to disable it.
"""

INVENIO_COLLECTIONS_UI_URL_PREFIX = "/collections"
"""URL prefix mounted by the collections UI blueprint."""
