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

from invenio_notifications.models import Notification, Recipient
from invenio_notifications.services.generators import RecipientGenerator
from invenio_records.dictutils import dict_lookup

from oarepo_communities.records.api import CommunityRoleRecord


class CommunityRoleEmailRecipient(RecipientGenerator):
    """Community role recipient generator for notifications."""

    def __init__(self, key: str):
        """Ctor."""
        self.key = key

    def __call__(self, notification: Notification, recipients: dict[str, Recipient]):
        """Update required recipient information and add backend id."""
        community_role = dict_lookup(notification.context, self.key)
        id_ = community_role["community"]["id"]
        role = community_role["role"]
        user_emails = CommunityRoleRecord.user_emails(id_, role)
        for user, email_data in user_emails.items():
            recipients[user] = Recipient(data=email_data)
