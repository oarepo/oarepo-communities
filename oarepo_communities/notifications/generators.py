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

from typing import Any

from invenio_accounts.models import User
from invenio_communities.members import MemberModel
from invenio_notifications.models import Recipient
from oarepo_requests.notifications.generators import SpecificEntityRecipient, _extract_entity_email_data


class CommunityRoleEmailRecipient(SpecificEntityRecipient):
    """Community role recipient generator for notifications."""

    # TODO: can member be a group? emails method suggested so
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
