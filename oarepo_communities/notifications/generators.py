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

from typing import TYPE_CHECKING

from invenio_communities.notifications.generators import CommunityMembersRecipient
from invenio_communities.proxies import current_roles
from invenio_notifications.services.generators import RecipientGenerator
from invenio_records.dictutils import dict_lookup
from invenio_requests.records import Request

if TYPE_CHECKING:
    from invenio_notifications.models import Notification, Recipient
    from invenio_requests.customizations import RequestType


class CommunityRoleEmailRecipient(RecipientGenerator):
    """Community role recipient generator for notifications."""

    def __init__(self, key: str):
        """Ctor."""
        self.key = key

    def __call__(self, notification: Notification, recipients: dict[str, Recipient]):
        """Update required recipient information and add backend id."""
        community_role = dict_lookup(notification.context, self.key)
        role = community_role["role"]

        invenio_generator = CommunityMembersRecipient(f"{self.key}.community", [role])
        return invenio_generator(notification, recipients)


class CommunityRecipient(RecipientGenerator):
    """Recipient generator for a community entity restricted to the members that can act on the request.

    Invenio's ``CommunityMembersRecipient`` notifies all members of a community when no roles are
    passed to it. As the receiver of a request is the party that decides about it, notifying all
    members leaks the request, and every comment on it, to members without any rights on it, e.g. a
    comment on a community membership request is delivered to every reader of the community.

    The notified roles are taken from the request type's ``needs_context`` (``community_roles``
    key), which is exactly the set of community roles the ``Receiver()`` permission generator maps
    the community receiver to (see ``CommunityPKProxy.get_needs``). If the request type does not
    declare any, the roles with management rights are used.
    """

    def __init__(self, key: str, request_key: str = "request", roles: list[str] | None = None):
        """Ctor.

        :param key: context key of the resolved community entity.
        :param request_key: context key of the resolved request the community roles are taken from.
        :param roles: community roles to notify. Derived from the request type if not given.
        """
        self.key = key
        self.request_key = request_key
        self.roles = roles

    def __call__(self, notification: Notification, recipients: dict[str, Recipient]):
        """Add the community members that can act on the request as recipients."""
        # the resolved roles are not stored on the instance: generators used directly by notification
        # builders are shared class attributes and must stay stateless
        roles = self.roles if self.roles is not None else self._community_roles(notification)
        return CommunityMembersRecipient(self.key, roles=roles)(notification, recipients)

    def _community_roles(self, notification: Notification) -> list[str]:
        """Return the community roles that can act on the request."""
        needs_context = getattr(self._request_type(notification), "needs_context", None) or {}
        roles = needs_context.get("community_roles")
        if roles:
            return [*roles]
        return [role.name for role in current_roles.can("manage")]

    def _request_type(self, notification: Notification) -> RequestType | None:
        """Return the type of the request the notification is about, if it can be determined."""
        try:
            request = dict_lookup(notification.context, self.request_key)
        except KeyError:
            return None
        if not isinstance(request, dict) or not request.get("id"):
            return None
        return Request.get_record(request["id"]).type
