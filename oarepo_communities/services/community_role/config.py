#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Service config for a community-role service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.records.results import RecordItem
from oarepo_workflows.services.results import InMemoryResultList

from oarepo_communities.records.api import CommunityRoleRecord

from .schema import CommunityRoleSchema

if TYPE_CHECKING:
    from collections.abc import Mapping


class CommunityRoleServiceConfig(ServiceConfig):
    """Service config for a community-role service."""

    service_id = "community-role"
    links_item: Mapping[str, Any] = {}

    record_cls = CommunityRoleRecord
    schema = CommunityRoleSchema

    result_item_cls = RecordItem
    result_list_cls = InMemoryResultList
