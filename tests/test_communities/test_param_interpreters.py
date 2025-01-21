from pytest_oarepo.communities.functions import invite


def test_community_role_param_interpreter(
    logged_client,
    community_owner,
    users,
    record_service,
    community_get_or_create,
    draft_with_community_factory,
    create_request_on_draft,
    submit_request_on_draft,
    search_clear,
):
    community_reader = users[0]
    community_curator = users[1]
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    community_3 = community_get_or_create(community_curator, "comm3")
    invite(community_reader, community_1.id, "reader")
    invite(community_reader, community_2.id, "reader")
    invite(community_reader, community_3.id, "reader")

    record1 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = draft_with_community_factory(community_owner.identity, str(community_2.id))
    record3 = draft_with_community_factory(
        community_owner.identity,
        str(community_2.id),
        custom_workflow="curator_publish",  # owner is creator but not receiver of the third request
    )

    response_1 = submit_request_on_draft(community_owner.identity, record1["id"], "publish_draft")
    response_2 = create_request_on_draft(community_owner.identity, record2["id"], "publish_draft")
    response_3 = submit_request_on_draft(community_owner.identity, record3["id"], "publish_draft")

    search_unfiltered = owner_client.get("/requests/")
    assert len(search_unfiltered.json["hits"]["hits"]) == 3

    search_filtered = owner_client.get("/requests/?assigned=true")

    assert len(search_filtered.json["hits"]["hits"]) == 0
