#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

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
from oarepo_communities.model.presets.communities.services.records.permission_policy import (
    CommunitiesPermissionPolicyPreset,
)
from oarepo_communities.model.presets.communities.services.records.service_config import (
    CommunitiesServiceConfigPreset,
)

communities_preset = [
    CommunitiesServiceConfigPreset,
    CommunitiesParentRecordSchemaPreset,
    ParentCommunityMetadataPreset,
    CommunitiesParentRecordPreset,
    CommunitiesPermissionPolicyPreset,
]
