#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Collection of workflow presets for configuring record models and services.

This module provides presets that handle different aspects of workflow-enabled records,
including draft support, service components, permissions, and schema definitions.
"""

from __future__ import annotations

from oarepo_communities.model.presets.communities.services.records.parent_record_schema import \
    CommunitiesParentRecordSchemaPreset
from oarepo_communities.model.presets.communities.services.records.service_config import CommunitiesServiceConfigPreset

communities_preset = [
    CommunitiesServiceConfigPreset,
    CommunitiesParentRecordSchemaPreset,
]