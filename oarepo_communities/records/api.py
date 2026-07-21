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
from typing import TYPE_CHECKING, Any

from invenio_access.models import Role, User
from invenio_communities.members.records.models import MemberModel
from invenio_db import db
from oarepo_requests.notifications.generators.recipients import _extract_user_email_data

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from invenio_communities.communities.records.api import Community


def _extract_user_email_data(user: User) -> dict[str, Any]:
    """Extract user email data from a User model.

    Note: should probably be replaced with invenio_users_resources' UserAggregate and schema.
    """
    return {
        "id": user.id,
        "preferences": dict(user.preferences) if user.preferences else user.preferences,
        "email": user.email,
    }


@dataclasses.dataclass
class CommunityRoleRecord:
    """A pseudo record representing a role within a community."""

    community: Community
    role: str

    @property
    def id(self) -> str:
        """Return the ID of the community role."""
        return f"{self.community.id}:{self.role}"

    @staticmethod
    def user_emails(community_id: str, role: str) -> dict[str, dict[str, Any]]:
        """Return the emails of the community members."""
        member_emails = {}
        members: list[MemberModel] = (
            db.session.query(MemberModel)
            .filter_by(
                community_id=community_id,
                role=role,
                active=True,
            )
            .all()
        )
        for member in members:
            try:
                if member.user_id:
                    user = User.query.get(member.user_id)
                    member_emails[user.id] = _extract_user_email_data(user)
                if member.group_id:
                    group = Role.query.get(member.group_id)
                    member_emails.update({user.id: (_extract_user_email_data(user)) for user in group.users})
            except Exception:
                log.exception(
                    "Error retrieving user %s, group %s for community members",
                    member.user_id,
                    member.group_id,
                )
        return member_emails

    # TODO: necessary?
    @property
    def emails(self) -> list[str]:
        """Return the emails of the community members."""
        return [email_data["email"] for email_data in self.user_emails(str(self.community.id), self.role).values()]
