def test_community_role_param_interpreter(
    logged_client,
    community_owner,
    community_reader,
    community_curator,
    community_with_workflow_factory,
    record_service,
    create_draft_via_resource,
    submit_request,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)
    curator_client = logged_client(community_curator)
    reader_client = logged_client(community_reader)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_curator)
    inviter("2", community_1.id, "reader")
    inviter("2", community_2.id, "reader")
    inviter("2", community_3.id, "reader")

    record1 = create_draft_via_resource(owner_client, community=community_1)
    record2 = create_draft_via_resource(owner_client, community=community_2)
    record3 = create_draft_via_resource(
        curator_client, community=community_3, custom_workflow="curator_publish"
    )

    response_1 = submit_request(reader_client, record1, "publish_draft")
    response_2 = submit_request(reader_client, record2, "publish_draft")
    response_3 = submit_request(owner_client, record3, "publish_draft")

    search_unfiltered = owner_client.get("/requests/")
    assert len(search_unfiltered.json["hits"]["hits"]) == 3

    search_filtered = owner_client.get("/requests/?assigned=true")

    assert len(search_filtered.json["hits"]["hits"]) == 2
