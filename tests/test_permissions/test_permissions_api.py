from thesis.resources.record_communities.config import (
    ThesisRecordCommunitiesResourceConfig,
)

RECORD_COMMUNITIES_BASE_URL = ThesisRecordCommunitiesResourceConfig.url_prefix


def _create_and_publish(client, input_data, community):
    """Create a draft and publish it."""
    # Create the draft
    response = client.post(RECORD_COMMUNITIES_BASE_URL, json=input_data)

    assert response.status_code == 201

    recid = response.json["id"]
    add = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/communities",
        json={
            "communities": [
                {"id": community.data["slug"]},  # test with slug
            ]
        },
    )
    # Publish it
    response = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/actions/publish"
    )
    return response


def test_owner(
    client,
    community_owner,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    owner_client = community_owner.login(client)
    record_resp = _create_and_publish(
        owner_client, input_data, community_with_permissions_cf
    )
    assert record_resp.status_code == 202
    recid = record_resp.json["id"]

    response_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{recid}")
    assert response_read.status_code == 200
    response_delete = owner_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{recid}")
    assert response_delete.status_code == 204
    response_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{recid}")
    assert response_read.status_code == 410


def test_cf(
    client,
    community_owner,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    community_owner.login(client)
    record_resp = _create_and_publish(client, input_data, community_with_permissions_cf)
    assert record_resp.status_code == 202
    recid = record_resp.json["id"]
    # sleep(5)
    response = client.get(f"{RECORD_COMMUNITIES_BASE_URL}{recid}/communities")
    assert (
        response.json["hits"]["hits"][0]["custom_fields"]
        == community_with_permissions_cf["custom_fields"]
    )


def test_reader(
    client,
    community_reader,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    reader_client = community_reader.login(client)
    record_resp = _create_and_publish(
        reader_client, input_data, community_with_permissions_cf
    )
    assert record_resp.status_code == 202
    recid = record_resp.json["id"]

    response_read = reader_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{recid}")
    assert response_read.status_code == 200
    response_delete = reader_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{recid}")
    assert response_delete.status_code == 403


def test_rando(
    client,
    rando_user,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    rando_client = rando_user.login(client)
    record_resp = _create_and_publish(
        rando_client, input_data, community_with_permissions_cf
    )
    assert record_resp.status_code == 403
