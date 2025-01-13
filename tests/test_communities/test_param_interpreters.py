def test_community_role_param_interpreter(
    logged_client,
    community_owner,
    users,
    community_with_workflow_factory,
    record_service,
    draft_with_community_factory,
    create_request_by_link,
    submit_request_by_link,
    inviter,
    search_clear,
):
    community_reader = users[0]
    community_curator = users[1]
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_curator)
    inviter(community_reader, community_1.id, "reader")
    inviter(community_reader, community_2.id, "reader")
    inviter(community_reader, community_3.id, "reader")

    record1 = draft_with_community_factory(owner_client, str(community_1.id))
    record2 = draft_with_community_factory(owner_client, str(community_2.id))
    record3 = draft_with_community_factory(
        owner_client,
        str(community_2.id),
        custom_workflow="curator_publish",  # owner is creator but not receiver of the third request
    )

    response_1 = submit_request_by_link(owner_client, record1, "publish_draft")
    response_2 = create_request_by_link(owner_client, record2, "publish_draft")
    response_3 = submit_request_by_link(owner_client, record3, "publish_draft")

    search_unfiltered = owner_client.get("/requests/")
    assert len(search_unfiltered.json["hits"]["hits"]) == 3

    search_filtered = owner_client.get("/requests/?assigned=true")

    assert len(search_filtered.json["hits"]["hits"]) == 0
