#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Community relations manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_communities.records.records.systemfields.communities.manager import (
    CommunitiesRelationManager as InvenioCommunitiesRelationManager,
)

from oarepo_communities.records.api import CommunityRoleRecord

if TYPE_CHECKING:
    import uuid

    from invenio_records_resources.records import Record


class CommunitiesRelationManager(InvenioCommunitiesRelationManager):
    """Manager for a record's community relations supporting community roles."""

    @override
    def _to_id(self, val: str | uuid.UUID | Record | CommunityRoleRecord) -> str | None:
        """Get the community id."""
        if isinstance(val, CommunityRoleRecord):
            return str(val.community.id)
        return super()._to_id(val)
