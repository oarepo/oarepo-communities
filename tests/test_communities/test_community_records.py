from invenio_access.permissions import system_identity
from thesis.records.api import ThesisDraft, ThesisRecord

from tests.test_communities.utils import published_record_in_community


def test_create_record_in_community(
    logged_client,
    init_cf,
    community_owner,
    community_with_default_workflow,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(
        f"/communities/{community_with_default_workflow.id}/thesis", json={}
    )
    assert response.json["parent"]["communities"]["ids"] == [
        community_with_default_workflow.id
    ]
    assert (
        response.json["parent"]["communities"]["default"]
        == community_with_default_workflow.id
    )

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [
        community_with_default_workflow.id
    ]
    assert (
        response_record.json["parent"]["communities"]["default"]
        == community_with_default_workflow.id
    )


def test_create_record_in_community_without_model_in_url(
    logged_client,
    community_owner,
    community_with_default_workflow,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(
        f"/communities/{community_with_default_workflow.id}/records",
        json={"$schema": "local://thesis-1.0.0.json"},
    )
    assert response.json["parent"]["communities"]["ids"] == [
        community_with_default_workflow.id
    ]
    assert (
        response.json["parent"]["communities"]["default"]
        == community_with_default_workflow.id
    )

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [
        community_with_default_workflow.id
    ]
    assert (
        response_record.json["parent"]["communities"]["default"]
        == community_with_default_workflow.id
    )


def test_search(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)

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


# todo tests for search links


def test_search_model(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)

    record1 = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )
    record2 = published_record_in_community(
        owner_client, community_2.id, record_service, community_owner
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/thesis")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/thesis")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_user_search(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    inviter("2", community_1.id, "reader")

    record1 = owner_client.post(f"/communities/{community_1.id}/thesis", json={}).json
    record2 = owner_client.post(f"/communities/{community_2.id}/thesis", json={}).json
    record3 = reader_client.post(f"/communities/{community_1.id}/thesis", json={}).json

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
    community_with_workflow_factory,
    record_service,
    inviter,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    inviter("2", community_1.id, "reader")

    record1 = owner_client.post(f"/communities/{community_1.id}/thesis", json={}).json
    record2 = owner_client.post(f"/communities/{community_2.id}/thesis", json={}).json
    record3 = reader_client.post(f"/communities/{community_1.id}/thesis", json={}).json

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/user/thesis")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/user/thesis")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_search_links(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    record_service,
    search_clear,
    site_hostname="127.0.0.1:5000",
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)

    for _ in range(30):
        published_record_in_community(
            owner_client, community_1.id, record_service, community_owner
        )
    ThesisRecord.index.refresh()
    def check_links(model_suffix):
        after_page_suffix = "&size=25&sort=newest"
        search_links = owner_client.get(
            f"/communities/{community_1.id}/{model_suffix}"
        ).json["links"]
        assert (
            search_links["self"]
            == f"https://{site_hostname}/api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"
        )
        assert (
            search_links["next"]
            == f"https://{site_hostname}/api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        )

        next_page = owner_client.get(
            f"/communities/{community_1.id}/{model_suffix}?page=2"
        ).json["links"]
        assert (
            next_page["self"]
            == f"https://{site_hostname}/api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        )
        assert (
            next_page["prev"]
            == f"https://{site_hostname}/api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"
        )


    check_links("records")
    check_links("thesis")
    check_links("user/records")
    check_links("user/thesis")

    search_links = owner_client.get(
        f"/communities/{community_1.id}/records?has_draft=true"
    ).json["links"]
    assert search_links["self"] == f"https://{site_hostname}/api/communities/{community_1.id}/records?has_draft=true&page=1&size=25&sort=newest"


def test_create_published(
    init_cf, community_owner, community_with_default_workflow, search_clear
):
    # todo how is workflow used in published service?
    from thesis.proxies import current_published_service

    record = current_published_service.create(system_identity, {"parent": {"communities": {"default": community_with_default_workflow.id}}})
    assert record._record.state == "published"
