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

from invenio_access.models import Role, User
from invenio_communities.members.records.models import MemberModel
from invenio_db import db
from oarepo_requests.notifications.generators import _extract_entity_email_data

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

    @property
    def emails(self) -> list[str]:
        """Return the emails of the community members."""
        member_emails = []
        members: list[MemberModel] = (
            db.session.query(MemberModel)
            .filter_by(
                community_id=self.community.id,
                role=self.role,
                active=True,
            )
            .all()
        )
        for member in members:
            try:
                if member.user_id:
                    user = User.query.get(member.user_id)
                    member_emails.append(_extract_entity_email_data(user))
                if member.group_id:
                    group = Role.query.get(member.group_id)
                    member_emails.extend(_extract_entity_email_data(user) for user in group.users)
            except Exception:
                log.exception(
                    "Error retrieving user %s, group %s for community members",
                    member.user_id,
                    member.group_id,
                )
        return member_emails
