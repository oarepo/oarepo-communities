#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import pytest
from invenio_access.models import User
from invenio_communities.members.records.models import MemberModel
from invenio_requests.customizations.event_types import CommentEventType
from pytest_oarepo.communities.functions import invite


@pytest.fixture
def events_service():
    from invenio_requests.proxies import current_events_service

    return current_events_service


def test_publish_notification_community_role(
    app,
    community,
    community_owner,
    users,
    logged_client,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
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


def test_notifications_not_sent_to_inactive_users(
    db,
    app,
    community,
    community_owner,
    users,
    logged_client,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
    search_clear,
):
    """Test notification being built on review submit."""
    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(users[2], str(community.id), "curator")

    member = MemberModel.query.filter_by(user_id=users[2].user.id, community_id=str(community.id)).one()
    member.active = False
    db.session.commit()

    us = User.query.join(MemberModel).filter(MemberModel.community_id == str(community.id)).all()
    active_users = (
        User.query.join(MemberModel)
        .filter((MemberModel.community_id == str(community.id)) & (MemberModel.active.is_(True)))
        .all()
    )

    assert users[2].user in us
    assert users[2].user not in active_users

    creator = users[0]
    draft1 = draft_with_community_factory(creator.identity, str(community.id), custom_workflow="curator_publish")
    with mail.record_messages() as outbox:
        submit_request_on_draft(creator.identity, draft1["id"], "publish_draft")
        # check notification is build on submit
        assert len(outbox) == 1  # only one curator active now
        assert outbox[0].send_to == {users[1].email}


def test_comment_notifications(
    app,
    users,
    logged_client,
    draft_with_community_factory,
    community,
    submit_request_on_draft,
    add_user_in_role,
    role,
    events_service,
    link2testclient,
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
