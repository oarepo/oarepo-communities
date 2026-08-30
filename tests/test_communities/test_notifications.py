#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_requests.customizations.event_types import CommentEventType


@pytest.fixture
def events_service():
    from invenio_requests.proxies import current_events_service

    return current_events_service


@pytest.fixture
def membership_request(requests_service, community, users):
    """Return a community membership request created by a user who is not a member of the community.

    The request is created by the system process on behalf of the user, because creating a request
    with a community topic is governed by the community's workflow.
    """
    requester = users[0]
    return requests_service.create(
        system_identity,
        data={"title": 'Request to join "My Community"'},
        request_type="community-membership-request",
        topic=community,
        receiver=community,
        creator={"user": str(requester.id)},
    )


def _recipients(outbox: list) -> set[str]:
    """Return all recipients of the mails sent in the given outbox."""
    return {recipient for mail in outbox for recipient in mail.recipients}


def test_publish_notification_community_role(
    app,
    community,
    community_owner,
    users,
    logged_client,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
    invite,
    search_clear,
):
    """Test notification being built on review submit."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(users[2], str(community.id), "curator")
    creator = users[0]

    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="curator_publish")
    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        # check notification is build on submit
        assert len(outbox) == 2  # both curators should get a mail
        recipients = outbox[0].send_to | outbox[1].send_to
        assert recipients == {"user2@example.org", "user3@example.org"}


def test_publish_notification_community_role_group(
    app,
    roles,
    add_user_in_role,
    community,
    users,
    draft_with_community_factory,
    submit_request_on_draft,
    invite,
    search_clear,
):
    """Test notification recipients when a community role is held by a group.

    The curator role is assigned to a user group rather than to individual
    members, so every user belonging to that group should get a mail.
    """
    mail = app.extensions.get("mail")
    assert mail

    group = roles[0]
    add_user_in_role(users[1], group)
    add_user_in_role(users[2], group)

    invite(users[0], str(community.id), "reader")
    current_communities.service.members.add(
        system_identity,
        str(community.id),
        {
            "members": [{"type": "group", "id": group.id}],
            "role": "curator",
            "visible": True,
        },
    )
    creator = users[0]

    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="curator_publish")
    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        # check notification is built on submit
        assert len(outbox) == 2  # both members of the curator group should get a mail
        recipients = outbox[0].send_to | outbox[1].send_to
        assert recipients == {users[1].email, users[2].email}


def test_publish_notification_community_role_user_and_group(
    app,
    roles,
    add_user_in_role,
    community,
    users,
    draft_with_community_factory,
    submit_request_on_draft,
    invite,
    search_clear,
):
    """Test notification recipients when a role is held by both a user and a group.

    The curator role is assigned to an individual member as well as to a user
    group, so the direct member and every user of the group should get a mail.
    """
    mail = app.extensions.get("mail")
    assert mail

    # Create a group and put two users into it.
    group = roles[0]
    add_user_in_role(users[2], group)
    add_user_in_role(users[3], group)

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")

    current_communities.service.members.add(
        system_identity,
        str(community.id),
        {
            "members": [{"type": "group", "id": group.id}],
            "role": "curator",
            "visible": True,
        },
    )
    creator = users[0]

    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="curator_publish")
    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        # check notification is built on submit
        assert len(outbox) == 3  # direct curator + both members of the curator group
        recipients = outbox[0].send_to | outbox[1].send_to | outbox[2].send_to
        assert recipients == {users[1].email, users[2].email, users[3].email}


def test_locales(
    app,
    community,
    users,
    user_with_cs_locale,
    logged_client,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
    invite,
    search_clear,
):
    """Test notification being built on review submit."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(user_with_cs_locale, str(community.id), "curator")
    creator = users[0]
    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="curator_publish")

    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        assert len(outbox) == 2
        sent_mail_cz = [mail for mail in outbox if mail.recipients[0] == user_with_cs_locale.user.email]
        sent_mail_en = [mail for mail in outbox if mail.recipients[0] == users[1].user.email]
        assert len(sent_mail_cz) == len(sent_mail_en) == 1
        assert sent_mail_cz[0].subject == "Žádost o publikování záznamu blabla"
        assert sent_mail_en[0].subject == "Request to publish record blabla"


def test_locales_multiple_recipients(
    app,
    community,
    community_owner,
    users,
    user_with_cs_locale,
    logged_client,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
    invite,
    search_clear,
):
    """Test notification being built on review submit."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(user_with_cs_locale, str(community.id), "curator")
    creator = users[0]
    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="multiple_recipients")

    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        assert len(outbox) == 2
        sent_mail_cz = [mail for mail in outbox if mail.recipients[0] == user_with_cs_locale.user.email]
        sent_mail_en = [mail for mail in outbox if mail.recipients[0] == community_owner.user.email]
        assert len(sent_mail_cz) == len(sent_mail_en) == 1
        assert sent_mail_cz[0].subject == "Žádost o publikování záznamu blabla"
        assert sent_mail_en[0].subject == "Request to publish record blabla"


def test_membership_request_comment_notifies_only_members_that_can_manage(
    app,
    community,
    membership_request,
    users,
    community_owner,
    invite,
    requests_events_service,
):
    """A comment on a community membership request is sent to the members that can accept it only.

    The requester writes the comment, so they are not notified about it. From the community members,
    only the owner and the manager, ie. the roles the receiver of the request maps to, are notified.
    """
    mail = app.extensions.get("mail")
    assert mail

    invite(users[1], str(community.id), "manager")
    invite(users[2], str(community.id), "curator")
    invite(users[3], str(community.id), "reader")

    with mail.record_messages() as outbox:
        requests_events_service.create(
            users[0].identity,
            membership_request["id"],
            {"payload": {"content": "We should talk about your membership."}},
            CommentEventType,
        )

    assert _recipients(outbox) == {community_owner.email, users[1].email}


def test_membership_request_comment_by_manager_notifies_requester(
    app,
    community,
    membership_request,
    users,
    community_owner,
    invite,
    requests_events_service,
):
    """A comment written by a community manager is sent to the requester, not to the manager."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[1], str(community.id), "manager")

    with mail.record_messages() as outbox:
        requests_events_service.create(
            users[1].identity,
            membership_request["id"],
            {"payload": {"content": "Welcome aboard."}},
            CommentEventType,
        )

    assert _recipients(outbox) == {users[0].email, community_owner.email}


def test_comment_notifications(
    app,
    users,
    logged_client,
    draft_with_community_factory,
    community,
    submit_request_on_draft,
    events_service,
    link2testclient,
    invite,
    urls,
):
    """Test notification being built on review submit."""
    mail = app.extensions.get("mail")
    creator = users[0]
    receiver = users[1]
    invite(users[0], str(community.id), "reader")
    invite(receiver, str(community.id), "curator")
    draft1 = draft_with_community_factory(
        creator.identity, str(community.id), custom_workflow="curator_publish"
    )  # so i don't have to create a new workflow
    submit = submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")

    with mail.record_messages() as outbox:
        content = "ceci nes pa une comment"
        events_service.create(
            creator.identity,
            submit["id"],
            {"payload": {"content": content}},
            CommentEventType,
        )
        assert len(outbox) == 1  # recipient of the request should get
        receivers = outbox[0].recipients
        assert set(receivers) == {receiver.email}
        assert content in outbox[0].body
