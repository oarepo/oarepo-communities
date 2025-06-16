from pytest_oarepo.communities.functions import invite


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

    draft1 = draft_with_community_factory(
        creator.identity, str(community.id), custom_workflow="curator_publish"
    )
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
):
    """Test notification being built on review submit."""

    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(users[1], str(community.id), "curator")
    invite(user_with_cs_locale, str(community.id), "curator")
    creator = users[0]
    draft1 = draft_with_community_factory(
        creator.identity, str(community.id), custom_workflow="curator_publish"
    )

    with mail.record_messages() as outbox:
        submit_request_on_draft(
            creator.identity, draft1["id"], "publish_draft"
        )
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
):
    """Test notification being built on review submit."""

    mail = app.extensions.get("mail")
    assert mail

    invite(users[0], str(community.id), "reader")
    invite(user_with_cs_locale, str(community.id), "curator")
    creator = users[0]
    draft1 = draft_with_community_factory(
        creator.identity, str(community.id), custom_workflow="multiple_recipients"
    )

    with mail.record_messages() as outbox:
        submit_request_on_draft(
            creator.identity, draft1["id"], "publish_draft"
        )
        assert len(outbox) == 2
        sent_mail_cz = [mail for mail in outbox if mail.recipients[0] == user_with_cs_locale.user.email]
        sent_mail_en = [mail for mail in outbox if mail.recipients[0] == community_owner.user.email]
        assert len(sent_mail_cz) == len(sent_mail_en) == 1
        assert sent_mail_cz[0].subject == "Žádost o publikování záznamu blabla"
        assert sent_mail_en[0].subject == "Request to publish record blabla"
