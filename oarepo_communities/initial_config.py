#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Default configuration for oarepo-communities to be initialized at invenio_config.module entrypoint."""

from __future__ import annotations

from oarepo_communities.requests.community_submission import CommunitySubmission
from oarepo_communities.services.community_records.service import (
    CommunityRecordsService,
)

RDM_RECORDS_COMMUNITY_RECORDS_SERVICE_CLASS = CommunityRecordsService
RDM_COMMUNITY_SUBMISSION_REQUEST_CLS = CommunitySubmission

INVENIO_COLLECTIONS_COMMUNITY_SLUG = "global"
"""Slug of the community that holds cross-repository ("global") collection trees.

When ``CommunityRecordsService.search`` is invoked for this community it omits
the ``parent.communities.ids`` filter, so a collection's own ``search_query``
resolves against every published record instead of only records tagged with the
holder community. Set to ``None`` in deployment config to disable this behavior.
"""

INVENIO_COLLECTIONS_UI_URL_PREFIX = "/collections"
"""URL prefix mounted by the collections UI blueprint."""
