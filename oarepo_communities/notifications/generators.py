#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module for communities related notifications generators."""

from __future__ import annotations

"""
from oarepo_requests.notifications.generators import SpecificEntityRecipient, _extract_entity_email_data
"""


# """Community role recipient generator for a notification."""
"""
class CommunityRoleEmailRecipient(SpecificEntityRecipient):


    def _get_recipients(self, entity: Any) -> dict[str, Recipient]:
        community_id = entity.community.id
        role = entity.role

        return {
            user.email: Recipient(data=_extract_entity_email_data(user))
            for user in (
                User.query.join(MemberModel)
                .filter(
                    MemberModel.role == role,
                    MemberModel.community_id == str(community_id),
                    MemberModel.active,
                )
                .all()
            )
        }
"""
