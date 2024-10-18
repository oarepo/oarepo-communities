

def test_community_role_param_interpreter(
    logged_client,
    community_owner,
    community_reader,
    community_curator,
    community_with_workflow_factory,
    record_service,
    create_draft_via_resource,
    create_request_by_link,
    submit_request_by_link,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_curator)
    inviter("2", community_1.id, "reader")
    inviter("2", community_2.id, "reader")
    inviter("2", community_3.id, "reader")

    record1 = create_draft_via_resource(owner_client, community=community_1)
    record2 = create_draft_via_resource(owner_client, community=community_2)
    record3 = create_draft_via_resource(
        owner_client, community=community_2, custom_workflow="curator_publish" # owner is creator but not receiver of the third request
    )

    response_1 = submit_request_by_link(owner_client, record1, "publish_draft")
    response_2 = create_request_by_link(owner_client, record2, "publish_draft")
    response_3 = submit_request_by_link(owner_client, record3, "publish_draft")

    search_unfiltered = owner_client.get("/requests/")
    assert len(search_unfiltered.json["hits"]["hits"]) == 3

    search_filtered = owner_client.get("/requests/?assigned=true")


    assert len(search_filtered.json["hits"]["hits"]) == 2
