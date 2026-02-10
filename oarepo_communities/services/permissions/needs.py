#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Need for user in community."""

from __future__ import annotations

from typing import NamedTuple


class UserInCommunityNeed(NamedTuple):
    """Need for user in community."""

    method: str
    value: str
    user: str | int
    community: str

    @classmethod
    def from_user_community(cls, user: str | int, community: str) -> UserInCommunityNeed:
        """Create need from user and community."""
        return cls("user_in_community", f"{user}:{community}", user, community)
