#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import pytest
from invenio_communities import current_communities


def _community_data(community) -> dict[str, Any]:
    return {
        "metadata": {
            "contributors": ["Contributor 1"],
            "creators": ["Creator 1", "Creator 2"],
            "title": "blabla",
        },
        "parent": {
            "communities": {"default": str(community.id)},
            "workflow": "default",
        },
    }


def test_review_process_and_community_submission(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    urls,
    upload_file,
    search_clear,
):
    community_id = str(community.id)
    community_reader = users[0]
    community_curator = users[1]
    invite(community_reader, community_id, "reader")
    invite(community_curator, community_id, "curator")
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    resp = reader_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "files": {"enabled": False},
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
        },  # must be here if communities are to customize who can create records
    )
    id_ = resp.json["id"]
    assert resp.json["parent"]["workflow"] is None
    assert not resp.json["parent"]["communities"]
    upload_file(
        identity=community_reader.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    review = reader_client.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )
    draft_read_after_review_create = reader_client.get(f"/records/{id_}/draft")
    assert draft_read_after_review_create.json["parent"]["workflow"] == "default"
    assert not resp.json["parent"]["communities"]

    assert "review" in draft_read_after_review_create.json["parent"]

    submit = reader_client.post(f"/records/{id_}/draft/actions/submit-review")

    curator_read = logged_client(community_curator).get(f"/requests/{review.json['id']}")
    owner_read = owner_client.get(f"/requests/{review.json['id']}")
    assert curator_read.status_code == 200
    assert owner_read.status_code == 200

    accept = owner_client.post(f"/requests/{review.json['id']}/actions/accept?expand=1")

    assert review.status_code == 200
    assert submit.status_code == 202
    assert accept.status_code == 200

    record = reader_client.get(f"/records/{id_}")
    assert record.status_code == 200
    assert record.json["parent"]["communities"]["default"] == community_id


def test_community_role_receiver(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    urls,
    upload_file,
    search_clear,
):
    community_id = str(community.id)
    community_reader = users[0]
    community_curator = users[1]
    invite(community_reader, community_id, "reader")
    invite(community_curator, community_id, "curator")
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    resp = reader_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
        },  # must be here if communities are to customize who can create records
    )
    id_ = resp.json["id"]
    assert resp.json["parent"]["workflow"] is None
    assert not resp.json["parent"]["communities"]
    upload_file(
        identity=community_reader.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    review = reader_client.put(
        f"/records/{id_}/draft/review",
        json={
            "receiver": {"community_role": f"{community_id}:owner"},
            "type": "community-submission",
        },
    )
    draft_read_after_review_create = reader_client.get(f"/records/{id_}/draft")
    assert draft_read_after_review_create.json["parent"]["workflow"] == "default"
    assert not resp.json["parent"]["communities"]

    assert "review" in draft_read_after_review_create.json["parent"]

    submit = reader_client.post(f"/records/{id_}/draft/actions/submit-review")

    curator_read = logged_client(community_curator).get(f"/requests/{review.json['id']}")
    owner_read = owner_client.get(f"/requests/{review.json['id']}")
    assert curator_read.status_code == 403
    assert owner_read.status_code == 200

    accept = owner_client.post(f"/requests/{review.json['id']}/actions/accept?expand=1")

    assert review.status_code == 200
    assert submit.status_code == 202
    assert accept.status_code == 200

    record = reader_client.get(f"/records/{id_}")
    assert record.status_code == 200
    assert record.json["parent"]["communities"]["default"] == community_id


def test_only_submitter_can_submit(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    urls,
    upload_file,
    search_clear,
):
    community_id = str(community.id)
    community_reader = users[0]
    community_submitter = users[1]
    invite(community_reader, community_id, "reader")
    invite(community_submitter, community_id, "submitter")
    reader_client = logged_client(community_reader)
    submitter_client = logged_client(community_submitter)

    resp = reader_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
            "parent": {"workflow": "community_submission_only_by_submitter"},
        },  # must be here if communities are to customize who can create records
    )
    id_ = resp.json["id"]
    assert resp.json["parent"]["workflow"] == "community_submission_only_by_submitter"
    assert not resp.json["parent"]["communities"]
    upload_file(
        identity=community_reader.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    reader_review = reader_client.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )

    submitter_review = submitter_client.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )
    assert reader_review.status_code == 403
    assert submitter_review.status_code == 200


def test_curator_auto_accept(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    urls,
    upload_file,
    search_clear,
):
    community_id = str(community.id)
    community_reader = users[0]
    community_curator = users[1]
    invite(community_reader, community_id, "reader")
    invite(community_curator, community_id, "curator")
    reader_client = logged_client(community_reader)
    community_curator = logged_client(community_curator)

    resp = reader_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
            "parent": {"workflow": "curator_auto_accept"},
        },  # must be here if communities are to customize who can create records
    )
    id_ = resp.json["id"]
    upload_file(
        identity=community_reader.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    review = community_curator.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )
    submit = community_curator.post(f"/records/{id_}/draft/actions/submit-review")


def test_links(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    urls,
    upload_file,
    link2testclient,
    search_clear,
):

    community_id = str(community.id)
    community_reader = users[0]
    invite(community_reader, community_id, "reader")
    reader_client = logged_client(community_reader)

    resp = reader_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
        },  # must be here if communities are to customize who can create records
    ).json
    id_ = resp["id"]
    reader_client.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )
    upload_file(
        identity=community_reader.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    record_after_review_create = reader_client.get(f"/records/{id_}/draft").json

    assert "review" in resp["links"]
    assert "submit-review" not in resp["links"]

    assert "review" in record_after_review_create["links"]
    assert "submit-review" in record_after_review_create["links"]

    assert link2testclient(record_after_review_create["links"]["review"]) == f"/records/{id_}/draft/review"
    assert (
        link2testclient(record_after_review_create["links"]["submit-review"])
        == f"/records/{id_}/draft/actions/submit-review"
    )


def test_create_record_in_community(logged_client, communities_model, community_owner, community, urls, search_clear):
    owner_client = logged_client(community_owner)
    response = owner_client.post(urls["BASE_URL"], json=_community_data(community))
    assert response.status_code == 201
    assert response.json["parent"]["communities"]["default"] == str(community.id)


def test_create_record_in_community_by_slug(
    logged_client, communities_model, community_owner, community, urls, search_clear
):
    owner_client = logged_client(community_owner)
    data = _community_data(community)
    data["parent"]["communities"]["default"] = community.slug
    response = owner_client.post(urls["BASE_URL"], json=data)
    assert response.status_code == 201
    assert response.json["parent"]["communities"]["default"] == str(community.id)


def test_create_record_in_community_default_workflow(
    logged_client, communities_model, community_owner, community, urls, search_clear
):
    owner_client = logged_client(community_owner)
    data = _community_data(community)
    del data["parent"]["workflow"]
    response = owner_client.post(urls["BASE_URL"], json=data)
    assert response.status_code == 201
    assert response.json["parent"]["communities"]["default"] == str(community.id)


def test_search(
    logged_client,
    communities_model,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    link2testclient,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    record1 = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = published_record_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

    response_record1 = owner_client.get(
        f"/records?q=parent.communities.default:{community_1.id}",
    )
    response_record2 = owner_client.get(
        f"/records?q=parent.communities.default:{community_2.id}",
    )

    response_draft1 = owner_client.get(f"/user/records?q=parent.communities.default:{community_1.id}")
    response_draft2 = owner_client.get(f"/user/records?q=parent.communities.default:{community_2.id}")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    # this now works as user search
    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_search_community_records(
    logged_client,
    communities_model,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    link2testclient,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    community1_item = current_communities.service.read(community_owner.identity, community_1.id)
    community2_item = current_communities.service.read(community_owner.identity, community_2.id)

    record1 = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = published_record_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

    response_record1 = owner_client.get(link2testclient(community1_item.links["records"]))
    response_record2 = owner_client.get(link2testclient(community2_item.links["records"]))

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


@pytest.mark.skip(reason="Search all not not implemented in RDM service")
def test_search_all(
    logged_client,
    communities_model,
    community_owner,
    published_record_with_community_factory,
    draft_with_community_factory,
    community_get_or_create,
    record_service,
    invite,
    users,
    search_clear,
):
    reader = users[0]
    curator = users[1]

    reader_client = logged_client(reader)
    curator_client = logged_client(curator)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(reader, community_1.id, "reader")
    invite(curator, community_1.id, "curator")

    owner_client = logged_client(community_owner)

    record1 = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = published_record_with_community_factory(community_owner.identity, str(community_2.id))

    draft1 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    draft2 = draft_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

    search_community1 = owner_client.get(f"/all/records?q=parent.communities.default:{community_1.id}")
    search_community2 = owner_client.get(f"/all/records?q=parent.communities.default:{community_2.id}")

    assert len(search_community1.json["hits"]["hits"]) == 2
    assert len(search_community2.json["hits"]["hits"]) == 2

    assert {hit["id"] for hit in search_community1.json["hits"]["hits"]} == {
        draft1["id"],
        record1["id"],
    }
    assert {hit["id"] for hit in search_community2.json["hits"]["hits"]} == {
        draft2["id"],
        record2["id"],
    }

    # test separate permissions
    curator_search = curator_client.get(f"/all/records?q=parent.communities.default:{community_1.id}")
    reader_search = reader_client.get(f"/all/records?q=parent.communities.default:{community_1.id}")

    assert len(curator_search.json["hits"]["hits"]) == 2
    assert len(reader_search.json["hits"]["hits"]) == 0


def test_search_model(
    logged_client,
    communities_model,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    record1 = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = published_record_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

    query1_url = urlencode(
        {"q": f'parent.communities.default:{community_1.id} AND $schema:"local://communities_test-v1.0.0.json"'}
    )
    query2_url = urlencode(
        {"q": f'parent.communities.default:{community_2.id} AND $schema:"local://communities_test-v1.0.0.json"'}
    )
    response_record1 = owner_client.get(f"/records?{query1_url}")
    response_record2 = owner_client.get(f"/records?{query2_url}")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_user_search(
    logged_client,
    communities_model,
    community_owner,
    users,
    draft_with_community_factory,
    community_get_or_create,
    invite,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, community_1.id, "reader")

    record1 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = draft_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

    query1_url = urlencode({"q": f"parent.communities.default:{community_1.id} AND record_status:published"})
    query2_url = urlencode({"q": f"parent.communities.default:{community_2.id} AND record_status:published"})

    response_record1 = owner_client.get(f"/user/records?{query1_url}")
    response_record2 = owner_client.get(f"/user/records?{query2_url}")

    response_draft1 = owner_client.get(f"/user/records?q=parent.communities.default:{community_1.id}")
    response_draft2 = owner_client.get(f"/user/records?q=parent.communities.default:{community_2.id}")

    assert len(response_record1.json["hits"]["hits"]) == 0
    assert len(response_record2.json["hits"]["hits"]) == 0

    assert len(response_draft1.json["hits"]["hits"]) == 1
    assert len(response_draft2.json["hits"]["hits"]) == 1

    assert response_draft1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_draft2.json["hits"]["hits"][0]["id"] == record2["id"]


def test_user_search_model(
    logged_client,
    communities_model,
    community_owner,
    users,
    draft_with_community_factory,
    community_get_or_create,
    record_service,
    invite,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, community_1.id, "reader")

    record1 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = draft_with_community_factory(community_owner.identity, str(community_2.id))

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()
    query1_url = urlencode(
        {"q": f'parent.communities.default:{community_1.id} AND $schema:"local://communities_test-v1.0.0.json"'}
    )
    query2_url = urlencode(
        {"q": f'parent.communities.default:{community_2.id} AND $schema:"local://communities_test-v1.0.0.json"'}
    )
    response_record1 = owner_client.get(f"/user/records?{query1_url}")
    response_record2 = owner_client.get(f"/user/records?{query2_url}")

    assert len(response_record1.json["hits"]["hits"]) == 1
    assert len(response_record2.json["hits"]["hits"]) == 1

    assert response_record1.json["hits"]["hits"][0]["id"] == record1["id"]
    assert response_record2.json["hits"]["hits"][0]["id"] == record2["id"]


@pytest.mark.skip(reason="Decide how the links should look.")
def test_search_links(
    logged_client,
    communities_model,
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
        published_record_with_community_factory(community_owner.identity, str(community_1.id))
    communities_model.Record.index.refresh()

    def check_links(model_suffix, sort_order) -> None:
        after_page_suffix = f"&size=25&sort={sort_order}"
        search_links = owner_client.get(f"/records?q=parent.communities.default:{community_1.id}").json["links"]
        assert (
            search_links["self"] == f"{host}api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"
        )
        assert (
            search_links["next"] == f"{host}api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        )

        next_page = owner_client.get(f"/communities/{community_1.id}/{model_suffix}?page=2").json["links"]
        assert next_page["self"] == f"{host}api/communities/{community_1.id}/{model_suffix}?page=2{after_page_suffix}"
        assert next_page["prev"] == f"{host}api/communities/{community_1.id}/{model_suffix}?page=1{after_page_suffix}"

    check_links("records", "newest")
    check_links("thesis", "newest")
    check_links("user/records", "updated-desc")
    check_links("user/thesis", "updated-desc")

    search_links = owner_client.get(f"/communities/{community_1.id}/records?has_draft=true").json["links"]
    assert (
        search_links["self"]
        == f"{host}api/communities/{community_1.id}/records?has_draft=true&page=1&size=25&sort=newest"
    )


@pytest.mark.skip
def test_search_ui_serialization(
    logged_client,
    communities_model,
    community_owner,
    published_record_with_community_factory,
    community_get_or_create,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    published_record_with_community_factory(community_owner.identity, community_1.id)
    published_record_with_community_factory(community_owner.identity, community_2.id)

    communities_model.Record.index.refresh()
    communities_model.Draft.index.refresh()

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

    # this was originally meant to determine the results go through ui serialization
    # ie. define something explicit in model json

    assert "access" in search_control.json["hits"]["hits"][0]
    assert "access" in search_global.json["hits"]["hits"][0]
    assert "access" in search_model.json["hits"]["hits"][0]
    assert "access" in search_user_global.json["hits"]["hits"][0]
    assert "access" in search_user_model.json["hits"]["hits"][0]
