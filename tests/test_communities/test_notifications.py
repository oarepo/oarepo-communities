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
    search_clear
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
        submit_request_on_draft(
            creator.identity, draft1["id"], "publish_draft"
        )
        # check notification is build on submit
        assert len(outbox) == 2  # both curators should get a mail
        recipients = outbox[0].send_to | outbox[1].send_to
        assert recipients == {"user2@example.org", "user3@example.org"}
