from thesis.records.api import ThesisDraft, ThesisRecord

from tests.test_communities.utils import published_record_in_community


def test_create_record_in_community(
    logged_client,
    community_owner,
    community_with_permissions_cf,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(
        f"/communities/{community_with_permissions_cf.id}/thesis/records", json={}
    )
    assert response.json["parent"]["communities"]["ids"] == [
        community_with_permissions_cf.id
    ]
    assert (
        response.json["parent"]["communities"]["default"]
        == community_with_permissions_cf.id
    )

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [
        community_with_permissions_cf.id
    ]
    assert (
        response_record.json["parent"]["communities"]["default"]
        == community_with_permissions_cf.id
    )


def test_create_record_in_community_without_model_in_url(
    logged_client,
    community_owner,
    community_with_permissions_cf,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(
        f"/communities/{community_with_permissions_cf.id}/records",
        json={"$schema": "local://thesis-1.0.0.json"},
    )
    assert response.json["parent"]["communities"]["ids"] == [
        community_with_permissions_cf.id
    ]
    assert (
        response.json["parent"]["communities"]["default"]
        == community_with_permissions_cf.id
    )

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [
        community_with_permissions_cf.id
    ]
    assert (
        response_record.json["parent"]["communities"]["default"]
        == community_with_permissions_cf.id
    )


def test_search(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)

    record1 = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )
    record2 = published_record_in_community(
        owner_client, community_2.id, record_service, community_owner
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/records")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/records")

    response_draft1 = owner_client.get(f"/communities/{community_1.id}/user/records")
    response_draft2 = owner_client.get(f"/communities/{community_2.id}/user/records")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    # this now works as user search
    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_search_model(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)

    record1 = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )
    record2 = published_record_in_community(
        owner_client, community_2.id, record_service, community_owner
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/thesis/records")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/thesis/records")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_user_search(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter("2", community_1.id, "reader")

    record1 = owner_client.post(
        f"/communities/{community_1.id}/thesis/records", json={}
    ).json
    record2 = owner_client.post(
        f"/communities/{community_2.id}/thesis/records", json={}
    ).json
    record3 = reader_client.post(
        f"/communities/{community_1.id}/thesis/records", json={}
    ).json

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/records")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/records")

    response_draft1 = owner_client.get(f"/communities/{community_1.id}/user/records")
    response_draft2 = owner_client.get(f"/communities/{community_2.id}/user/records")

    assert len(response_record1.json["hits"]["hits"]) == 0
    assert len(response_record2.json["hits"]["hits"]) == 0

    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_draft1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_draft2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_user_search_model(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    record_service,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter("2", community_1.id, "reader")

    record1 = owner_client.post(
        f"/communities/{community_1.id}/thesis/records", json={}
    ).json
    record2 = owner_client.post(
        f"/communities/{community_2.id}/thesis/records", json={}
    ).json
    record3 = reader_client.post(
        f"/communities/{community_1.id}/thesis/records", json={}
    ).json

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(
        f"/communities/{community_1.id}/user/thesis/records"
    )
    response_record2 = owner_client.get(
        f"/communities/{community_2.id}/user/thesis/records"
    )

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]
