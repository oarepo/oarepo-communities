# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
