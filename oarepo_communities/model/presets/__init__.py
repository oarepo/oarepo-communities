# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OARepo model presets for communities."""

from __future__ import annotations

from oarepo_communities.model.presets.communities.records.parent_community import (
    ParentCommunityMetadataPreset,
)
from oarepo_communities.model.presets.communities.records.parent_record import (
    CommunitiesParentRecordPreset,
)
from oarepo_communities.model.presets.communities.services.records.parent_record_schema import (
    CommunitiesParentRecordSchemaPreset,
)
from oarepo_communities.model.presets.communities.services.records.service_config import (
    CommunitiesServiceConfigPreset,
)

communities_preset = [
    CommunitiesServiceConfigPreset,
    CommunitiesParentRecordSchemaPreset,
    ParentCommunityMetadataPreset,
    CommunitiesParentRecordPreset,
]
