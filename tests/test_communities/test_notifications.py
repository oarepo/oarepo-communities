# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity
from invenio_communities.notifications.builders import (
    CommunityMembershipRequestSubmittedNotificationBuilder,
)
from invenio_communities.proxies import current_communities
from invenio_notifications.proxies import current_notifications_manager
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


def test_membership_request_notification_uses_local_template(
    app,
    membership_request,
    community_owner,
    requests_service,
    search_clear,
    users,
):
    """Render the local membership-request template through the live mail backend."""
    notification = CommunityMembershipRequestSubmittedNotificationBuilder.build(
        request=requests_service.record_cls.get_record(membership_request["id"]),
        role="reader",
        message="I would like to join.",
    )
    mail = app.extensions["mail"]

    with mail.record_messages() as outbox:
        current_notifications_manager.handle_broadcast(notification)

    assert len(outbox) == 1
    sent_mail = outbox[0]
    requester_name = f"User {users[0].id}"
    assert sent_mail.recipients == [community_owner.email]
    assert sent_mail.subject == f"📬 New request from '{requester_name}' to join the community 'My Community'"
    assert f"'{requester_name}' wants to join the community 'My Community'" in sent_mail.body
    assert "I would like to join." in sent_mail.body
    assert f"@{requester_name}" not in sent_mail.body


def test_submit_review_notification_community_role(
    app,
    community,
    community_owner,
    users,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """The members that can curate the community get a mail on review submit, the submitter does not."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(users[2], str(community.id), "curator")
    invite(users[3], str(community.id), "reader")
    submitter = users[0]

    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    with mail.record_messages() as outbox:
        submit_review(submitter.identity, draft["id"])

    assert _recipients(outbox) == {community_owner.email, users[1].email, users[2].email}


def test_submit_review_notification_community_role_group(
    app,
    roles,
    add_user_in_role,
    community,
    community_owner,
    users,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """Every user of a group holding the curator role gets a mail on review submit."""
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
    submitter = users[0]

    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    with mail.record_messages() as outbox:
        submit_review(submitter.identity, draft["id"])

    assert _recipients(outbox) == {community_owner.email, users[1].email, users[2].email}


def test_submit_review_notification_community_role_user_and_group(
    app,
    roles,
    add_user_in_role,
    community,
    community_owner,
    users,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """Both the direct curator and the users of a group holding the curator role get a mail on review submit."""
    mail = app.extensions.get("mail")
    assert mail

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
    submitter = users[0]

    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    with mail.record_messages() as outbox:
        submit_review(submitter.identity, draft["id"])

    assert _recipients(outbox) == {community_owner.email, users[1].email, users[2].email, users[3].email}


def test_locales(
    app,
    community,
    community_owner,
    users,
    user_with_cs_locale,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """The review submit mail is rendered in the locale of each recipient."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(user_with_cs_locale, str(community.id), "curator")
    submitter = users[0]
    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))

    with mail.record_messages() as outbox:
        submit_review(submitter.identity, draft["id"])

    subjects = {sent_mail.recipients[0]: sent_mail.subject for sent_mail in outbox}
    assert subjects == {
        user_with_cs_locale.email: "📥 Nový záznam byl odeslán do vaší komunity 'My Community'",
        users[1].email: "📥 New record submission to your community 'My Community'",
        community_owner.email: "📥 New record submission to your community 'My Community'",
    }


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
    community,
    community_owner,
    draft_with_community_submission_factory,
    submit_review,
    events_service,
    invite,
    search_clear,
):
    """A comment on a review is sent to the community members that can curate it, not to its author."""
    mail = app.extensions.get("mail")
    assert mail
    submitter = users[0]
    curator = users[1]
    invite(submitter, str(community.id), "reader")
    invite(curator, str(community.id), "curator")
    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    review = submit_review(submitter.identity, draft["id"])

    content = "ceci nes pa une comment"
    with mail.record_messages() as outbox:
        events_service.create(
            submitter.identity,
            review["id"],
            {"payload": {"content": content}},
            CommentEventType,
        )

    assert _recipients(outbox) == {curator.email, community_owner.email}
    assert all(content in sent_mail.body for sent_mail in outbox)
