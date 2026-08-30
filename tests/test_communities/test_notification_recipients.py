#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests of the recipient generator used for community entities.

The generator replaces Invenio's plain ``CommunityMembersRecipient``, which notifies all members of a
community. Only the members that can act on the request should learn about it, which is what these
tests check, together with the registration of the generator for the ``community`` entity type.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from oarepo_communities import config as oarepo_communities_config
from oarepo_communities.notifications import generators as generators_module
from oarepo_communities.notifications.generators import (
    CommunityRecipient,
    CommunityRoleEmailRecipient,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask import Flask
    from invenio_notifications.models import Notification


def _registry() -> dict:
    """Return the recipient generator registry used to resolve receivers of requests.

    The registry is owned by oarepo-requests, but it is filled in from the merged
    ``NOTIFICATION_RECIPIENTS_RESOLVERS`` configuration.
    """
    from oarepo_requests.proxies import current_notification_recipient_generators_registry

    return dict(current_notification_recipient_generators_registry)


#
# Registration of the community recipient generator
#


def test_community_generator_is_provided_by_the_configuration() -> None:
    """The community recipient generator is part of the configuration defaults."""
    resolver = oarepo_communities_config.NOTIFICATION_RECIPIENTS_RESOLVERS["community"]
    assert isinstance(resolver("request.receiver", None), CommunityRecipient)


def test_community_generator_is_used(app: Flask) -> None:
    """Community entities are resolved by the recipient generator of this library."""
    assert isinstance(_registry()["community"]("request.receiver", None), CommunityRecipient)


def test_generator_for_community_role_is_untouched(app: Flask) -> None:
    """Adding the community generator does not change how community roles are resolved."""
    assert isinstance(_registry()["community_role"]("receiver", None), CommunityRoleEmailRecipient)


#
# Community recipient roles
#


@pytest.fixture
def recorded_roles(monkeypatch: pytest.MonkeyPatch) -> list[list[str] | None]:
    """Capture the community roles the members recipient is created with."""
    calls: list[list[str] | None] = []

    def _community_members_recipient(_key: str, roles: list[str] | None = None) -> Callable[[Notification, dict], dict]:
        # the real CommunityMembersRecipient is constructed and then called with the notification
        calls.append(roles)
        return lambda _notification, recipients: recipients

    monkeypatch.setattr(generators_module, "CommunityMembersRecipient", _community_members_recipient)
    return calls


@pytest.fixture
def notification() -> Notification:
    """Return a notification with a resolved request and a community receiver."""
    from invenio_notifications.models import Notification

    return Notification(
        type="comment-request-event.create",
        context={
            "request": {"id": "request-id", "receiver": {"community": "community-id"}},
            "request.receiver": {"id": "community-id", "slug": "my-community"},
        },
    )


def _patch_request_type(monkeypatch: pytest.MonkeyPatch, needs_context: dict | None) -> None:
    """Make the request of the notification resolve to a request type with the given needs context."""
    request_type = SimpleNamespace(needs_context=needs_context)
    record = SimpleNamespace(type=request_type)
    monkeypatch.setattr(generators_module, "Request", SimpleNamespace(get_record=lambda _id: record))


def _patch_manage_roles(monkeypatch: pytest.MonkeyPatch, roles: list[str]) -> None:
    """Make the community role registry report the given roles as the ones that can manage."""
    monkeypatch.setattr(
        generators_module,
        "current_roles",
        SimpleNamespace(can=lambda _action: [SimpleNamespace(name=role) for role in roles]),
    )


def test_roles_are_taken_from_the_request_type_needs_context(
    monkeypatch: pytest.MonkeyPatch,
    recorded_roles: list[list[str] | None],
    notification: Notification,
) -> None:
    """Only the community roles that can act on the request are notified."""
    _patch_request_type(monkeypatch, {"community_roles": ["owner", "manager"]})

    CommunityRecipient("request.receiver")(notification, {})

    assert recorded_roles == [["owner", "manager"]]


def test_roles_fall_back_to_manage_roles(
    monkeypatch: pytest.MonkeyPatch,
    recorded_roles: list[list[str] | None],
    notification: Notification,
) -> None:
    """Without community roles on the request type, the roles with manage rights are notified."""
    _patch_request_type(monkeypatch, None)
    _patch_manage_roles(monkeypatch, ["manager", "owner"])

    CommunityRecipient("request.receiver")(notification, {})

    assert recorded_roles == [["manager", "owner"]]


def test_roles_fall_back_to_manage_roles_without_a_request(
    monkeypatch: pytest.MonkeyPatch,
    recorded_roles: list[list[str] | None],
    notification: Notification,
) -> None:
    """A notification which does not describe a request does not blow up on the missing one."""
    _patch_manage_roles(monkeypatch, ["manager", "owner"])
    notification.context = {"request.receiver": {"id": "community-id"}}

    CommunityRecipient("request.receiver")(notification, {})

    assert recorded_roles == [["manager", "owner"]]


def test_explicitly_configured_roles_win(
    monkeypatch: pytest.MonkeyPatch,
    recorded_roles: list[list[str] | None],
    notification: Notification,
) -> None:
    """Roles given to the generator are used as they are."""
    _patch_request_type(monkeypatch, {"community_roles": ["owner", "manager"]})

    CommunityRecipient("request.receiver", roles=["owner"])(notification, {})

    assert recorded_roles == [["owner"]]


def test_generator_does_not_keep_resolved_roles(
    monkeypatch: pytest.MonkeyPatch,
    recorded_roles: list[list[str] | None],
    notification: Notification,
) -> None:
    """A single generator instance can be reused for notifications of different request types.

    Generators are shared as notification builder class attributes, so resolving the roles must not
    leak from one notification to the next one.
    """
    _patch_request_type(monkeypatch, {"community_roles": ["owner"]})
    generator = CommunityRecipient("request.receiver")

    generator(notification, {})
    _patch_request_type(monkeypatch, {"community_roles": ["owner", "manager"]})
    generator(notification, {})

    assert recorded_roles == [["owner"], ["owner", "manager"]]
