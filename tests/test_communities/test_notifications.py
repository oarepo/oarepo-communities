from .conftest import link_api2testclient
from .utils import pick_request_type


def test_publish_accept_notification_community_role(
    app,
    community,
    community_owner,
    user_factory,
    logged_client,
    create_draft_via_resource,
):
    """Test notification being built on review submit."""

    mail = app.extensions.get("mail")
    assert mail

    reader = user_factory("rea1", (str(community.id), "reader"))
    curator_1 = user_factory("cur1", (str(community.id), "curator"))
    curator_2 = user_factory("cur2", (str(community.id), "curator"))

    creator = reader
    receiver = community_owner

    creator_client = logged_client(creator)
    receiver_client = logged_client(receiver)

    draft1 = create_draft_via_resource(creator_client, community=community, custom_workflow="curator_publish", expand=True)
    request_types = creator_client.get(link_api2testclient(draft1.json["links"]["applicable-requests"])).json["hits"]["hits"]
    link = link_api2testclient(
        pick_request_type(request_types, "publish_draft")[
            "links"
        ]["actions"]["create"]
    )
    resp_request_create = creator_client.post(
        link, json={"payload": {"version": "1.0"}}
    )
    with mail.record_messages() as outbox:
        resp_request_submit = creator_client.post(
            link_api2testclient(resp_request_create.json["links"]["actions"]["submit"]),
        )
        assert len(outbox) == 2 # both curators should get a mail
        recipients = outbox[0].send_to | outbox[1].send_to
        assert recipients == {"cur1@inveniosoftware.org", "cur2@inveniosoftware.org"}
