#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extra communities records."""

from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from invenio_communities.communities.records.api import Community


@dataclasses.dataclass
class CommunityRoleRecord:
    """A pseudo record representing a role within a community."""

    community: Community
    role: str

    @property
    def id(self) -> str:
        """Return the ID of the community role."""
        return f"{self.community.id}:{self.role}"
