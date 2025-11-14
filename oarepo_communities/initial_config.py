#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Default configuration for oarepo-communities to be initialized at invenio_config.module entrypoint."""

from __future__ import annotations

from oarepo_communities.services.community_records.service import CommunityRecordsService

RDM_RECORDS_COMMUNITY_RECORDS_SERVICE_CLASS = CommunityRecordsService
