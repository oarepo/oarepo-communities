#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for `oarepo_communities.ext.fix_hardcoded_roles`.

These target a real bug: several `invenio_communities`/`invenio_rdm_records` request types
and notification builders hard-code the stock `"manager"`/`"curator"` role names instead of
reading the roles actually configured via `COMMUNITIES_ROLES`. `fix_hardcoded_roles` patches
those classes at app-finalization time. Because the patched classes are process-global, the
tests snapshot and restore their state so they don't leak into other tests in the suite.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import pytest
from flask import Flask
from invenio_communities.members.services.request import (
    CommunityInvitation,
    MembershipRequestRequestType,
)
from invenio_communities.notifications import builders as community_notification_builders
from invenio_communities.notifications.generators import CommunityMembersRecipient
from invenio_communities.subcommunities.services.request import (
    SubCommunityInvitationRequest,
    SubCommunityRequest,
)
from invenio_notifications.services.generators import ConditionalRecipientGenerator
from invenio_rdm_records.notifications import builders as rdm_notification_builders
from invenio_rdm_records.requests.community_inclusion import CommunityInclusion
from invenio_rdm_records.requests.community_submission import CommunitySubmission

from oarepo_communities.ext import fix_hardcoded_roles

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.usefixtures("_restore_hardcoded_role_state")

REQUEST_TYPES = (
    CommunityInvitation,
    MembershipRequestRequestType,
    SubCommunityRequest,
    SubCommunityInvitationRequest,
    CommunityInclusion,
    CommunitySubmission,
)

NOTIFICATION_MODULES = (community_notification_builders, rdm_notification_builders)

CUSTOM_ROLES = [
    {"name": "reader", "can_manage": False, "can_curate": False},
    {"name": "curator", "can_manage": True, "can_curate": True},
    {"name": "owner", "can_manage": True, "can_curate": True, "is_owner": True},
]
"""A role set that, unlike Invenio's stock roles, has no role literally named "manager"."""


def _iter_community_members_recipients(recipients: list | None) -> Iterator[CommunityMembersRecipient]:
    """Recursively yield `CommunityMembersRecipient` instances, including nested ones."""
    for recipient in recipients or []:
        if isinstance(recipient, CommunityMembersRecipient):
            yield recipient
        elif isinstance(recipient, ConditionalRecipientGenerator):
            yield from _iter_community_members_recipients(recipient.then_)
            yield from _iter_community_members_recipients(recipient.else_)


def _all_community_members_recipients() -> Iterator[CommunityMembersRecipient]:
    for module in NOTIFICATION_MODULES:
        for builder in vars(module).values():
            if isinstance(builder, type):
                yield from _iter_community_members_recipients(getattr(builder, "recipients", None))


@pytest.fixture
def _restore_hardcoded_role_state() -> Iterator[None]:
    """Snapshot process-global state mutated by `fix_hardcoded_roles` and restore it after the test."""
    needs_context_snapshot = {request_type: copy.deepcopy(request_type.needs_context) for request_type in REQUEST_TYPES}
    roles_snapshot = [(recipient, list(recipient.roles)) for recipient in _all_community_members_recipients()]
    yield
    for request_type, needs_context in needs_context_snapshot.items():
        request_type.needs_context = needs_context
    for recipient, roles in roles_snapshot:
        recipient.roles = roles


def _fake_app(communities_roles: list[dict]) -> Flask:
    app = Flask("test_fix_hardcoded_roles")
    app.config["COMMUNITIES_ROLES"] = communities_roles
    return app


def test_replaces_manager_and_curator_in_request_types():
    """Category A: request types that gate accept/decline/cancel/expire on community roles."""
    app = _fake_app(CUSTOM_ROLES)

    fix_hardcoded_roles(app)

    assert CommunityInvitation.needs_context == {"community_roles": ["curator", "owner"]}
    assert MembershipRequestRequestType.needs_context == {"community_roles": ["curator", "owner"]}
    assert SubCommunityRequest.needs_context == {"community_roles": ["curator", "owner"]}
    assert SubCommunityInvitationRequest.needs_context == {"community_roles": ["curator", "owner"]}
    # these also carry a "record_permission" key that must survive untouched
    assert CommunityInclusion.needs_context == {
        "community_roles": ["curator", "owner"],
        "record_permission": "preview",
    }
    assert CommunitySubmission.needs_context == {
        "community_roles": ["curator", "owner"],
        "record_permission": "preview",
    }


def test_replaces_manager_and_curator_in_notification_recipients():
    """Category C: notification recipients, including ones nested inside `IfUserRecipient`."""
    app = _fake_app(CUSTOM_ROLES)

    fix_hardcoded_roles(app)

    assert community_notification_builders.CommunityInvitationAcceptNotificationBuilder.recipients[0].roles == [
        "curator",
        "owner",
    ]
    assert rdm_notification_builders.CommunityInclusionNotificationBuilder.recipients[0].roles == [
        "curator",
        "owner",
    ]
    assert rdm_notification_builders.CommunityInclusionCancelNotificationBuilder.recipients[0].roles == [
        "curator",
        "owner",
    ]

    # roles=["curator", "owner"] here sits inside IfUserRecipient(..., else_=[CommunityMembersRecipient(...)])
    guest_recipient = rdm_notification_builders.GuestAccessRequestSubmitNotificationBuilder.recipients[0]
    assert guest_recipient.else_[0].roles == ["curator", "owner"]
    user_recipient = rdm_notification_builders.UserAccessRequestSubmitNotificationBuilder.recipients[0]
    assert user_recipient.else_[0].roles == ["curator", "owner"]


def test_preserves_other_roles_already_in_the_list():
    """Roles other than "manager"/"curator" (e.g. "owner", or a role Invenio might add later) are kept."""
    app = _fake_app(CUSTOM_ROLES)
    CommunityInvitation.needs_context = {"community_roles": ["owner", "manager", "some-future-role"]}

    fix_hardcoded_roles(app)

    assert CommunityInvitation.needs_context == {"community_roles": ["curator", "owner", "some-future-role"]}


def test_is_idempotent():
    app = _fake_app(CUSTOM_ROLES)

    fix_hardcoded_roles(app)
    needs_context_after_first_call = copy.deepcopy(CommunityInclusion.needs_context)
    roles_after_first_call = list(rdm_notification_builders.CommunityInclusionNotificationBuilder.recipients[0].roles)

    fix_hardcoded_roles(app)

    assert CommunityInclusion.needs_context == needs_context_after_first_call
    assert rdm_notification_builders.CommunityInclusionNotificationBuilder.recipients[0].roles == roles_after_first_call


def test_noop_when_roles_are_not_configured():
    app = _fake_app([])
    accept_notification_builder = community_notification_builders.CommunityInvitationAcceptNotificationBuilder
    needs_context_before = copy.deepcopy(CommunityInvitation.needs_context)
    roles_before = list(accept_notification_builder.recipients[0].roles)

    fix_hardcoded_roles(app)

    assert CommunityInvitation.needs_context == needs_context_before
    assert accept_notification_builder.recipients[0].roles == roles_before
