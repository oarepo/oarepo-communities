from pytest_oarepo.communities.functions import invite
from thesis.records.api import ThesisDraft, ThesisRecord


def test_create_record_in_community(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(f"/communities/{community.id}/thesis", json={})
    assert response.json["parent"]["communities"]["ids"] == [community.id]
    assert response.json["parent"]["communities"]["default"] == community.id

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [community.id]
    assert response_record.json["parent"]["communities"]["default"] == community.id


def test_create_record_in_community_without_model_in_url(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(
        f"/communities/{community.id}/records",
        json={"$schema": "local://thesis-1.0.0.json"},
    )
    assert response.json["parent"]["communities"]["ids"] == [community.id]
    assert response.json["parent"]["communities"]["default"] == community.id

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [community.id]
    assert response_record.json["parent"]["communities"]["default"] == community.id


def test_search(
    logged_client,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    record1 = published_record_with_community_factory(
        community_owner.identity, community_1.id
    )
    record2 = published_record_with_community_factory(
        community_owner.identity, community_2.id
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(
        f"/communities/{community_1.id}/records",
        query_string={"record_status": "published"},
    )
    response_record2 = owner_client.get(
        f"/communities/{community_2.id}/records",
        query_string={"record_status": "published"},
    )

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
    logged_client,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    record1 = published_record_with_community_factory(
        community_owner.identity, community_1.id
    )
    record2 = published_record_with_community_factory(
        community_owner.identity, community_2.id
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
    logged_client,
    community_owner,
    users,
    draft_with_community_factory,
    community_get_or_create,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, community_1.id, "reader")

    record1 = draft_with_community_factory(
        community_owner.identity, str(community_1.id)
    )
    record2 = draft_with_community_factory(
        community_owner.identity, str(community_2.id)
    )
    record3 = draft_with_community_factory(
        community_reader.identity, str(community_1.id)
    )

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
    logged_client,
    community_owner,
    users,
    draft_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, community_1.id, "reader")

    record1 = draft_with_community_factory(
        community_owner.identity, str(community_1.id)
    )
    record2 = draft_with_community_factory(
        community_owner.identity, str(community_2.id)
    )
    record3 = draft_with_community_factory(
        community_reader.identity, str(community_1.id)
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = owner_client.get(f"/communities/{community_1.id}/user/thesis")
    response_record2 = owner_client.get(f"/communities/{community_2.id}/user/thesis")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_search_links(
    logged_client,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    host,
    search_clear,
):

    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")

    for _ in range(30):
        published_record_with_community_factory(
            community_owner.identity, community_1.id
        )
    ThesisRecord.index.refresh()

    def check_links(model_suffix):
        after_page_suffix = "&size=25&sort=newest"
        search_links = owner_client.get(
            f"/communities/{community_1.id}/{model_suffix}"
        ).json["links"]
        assert (
            search_links["self"]
            == f"{host}api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"
        )
        assert (
            search_links["next"]
            == f"{host}api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        )

        next_page = owner_client.get(
            f"/communities/{community_1.id}/{model_suffix}?page=2"
        ).json["links"]
        assert (
            next_page["self"]
            == f"{host}api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        )
        assert (
            next_page["prev"]
            == f"{host}api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"
        )

    check_links("records")
    check_links("thesis")
    check_links("user/records")
    check_links("user/thesis")

    search_links = owner_client.get(
        f"/communities/{community_1.id}/records?has_draft=true"
    ).json["links"]
    assert (
        search_links["self"]
        == f"{host}api/communities/{community_1.id}/records?has_draft=true&page=1&size=25&sort=newest"
    )


def test_search_ui_serialization(
    logged_client,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    record1 = published_record_with_community_factory(
        community_owner.identity, community_1.id
    )
    record2 = published_record_with_community_factory(
        community_owner.identity, community_2.id
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    search_control = owner_client.get(f"/communities/{community_1.id}/records")
    search_global = owner_client.get(
        f"/communities/{community_1.id}/records",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    search_model = owner_client.get(
        f"/communities/{community_2.id}/thesis",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )

    search_user_global = owner_client.get(
        f"/communities/{community_1.id}/user/records",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    search_user_model = owner_client.get(
        f"/communities/{community_2.id}/user/thesis",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )

    assert search_global.status_code == 200
    assert search_model.status_code == 200
    assert search_user_global.status_code == 200
    assert search_user_model.status_code == 200

    # todo ui serialization is now recognizable through filtering parent - this might not make sense in the future
    # ie. define something explicit in model json
    assert "parent" in search_control.json["hits"]["hits"][0]
    assert "parent" not in search_global.json["hits"]["hits"][0]
    assert "parent" not in search_model.json["hits"]["hits"][0]
    assert "parent" not in search_user_global.json["hits"]["hits"][0]
    assert "parent" not in search_user_model.json["hits"]["hits"][0]


"""
# todo published service conceptual rework
def test_create_published(community_owner, community, search_clear):
    # todo how is workflow used in published service?
    from thesis.proxies import current_published_service

    record = current_published_service.create(
        system_identity, {"parent": {"communities": {"default": community.id}}}
    )
    assert record._record.state == "published"
"""
