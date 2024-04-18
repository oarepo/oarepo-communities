from thesis.records.api import ThesisDraft, ThesisRecord

from tests.test_communities.utils import published_record_in_community


def test_create_record_in_community(
    client_factory,
    community_owner,
    community_with_permissions_cf,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

    response = owner_client.post(
        f"/communities/{community_with_permissions_cf.id}/records", json={}
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
    client_factory,
    community_owner,
    community_with_permission_cf_factory,
    record_service,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

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

    response_draft1 = owner_client.get(f"/communities/{community_1.id}/draft/records")
    response_draft2 = owner_client.get(f"/communities/{community_2.id}/draft/records")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    # this now works as user search
    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_search_drafts(
    client_factory,
    community_owner,
    community_with_permission_cf_factory,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)

    record1 = owner_client.post(f"/communities/{community_1.id}/records", json={}).json
    record2 = owner_client.post(f"/communities/{community_2.id}/records", json={}).json

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/records")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/records")

    response_draft1 = owner_client.get(f"/communities/{community_1.id}/draft/records")
    response_draft2 = owner_client.get(f"/communities/{community_2.id}/draft/records")

    assert len(response_record1.json["hits"]["hits"]) == 0
    assert len(response_record2.json["hits"]["hits"]) == 0

    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_draft1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_draft2.json["hits"]["hits"][0]["id"] == record2["id"]
