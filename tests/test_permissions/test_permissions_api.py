from thesis.records.api import ThesisDraft
from thesis.resources.record_communities.config import (
    ThesisRecordCommunitiesResourceConfig,
)

RECORD_COMMUNITIES_BASE_URL = ThesisRecordCommunitiesResourceConfig.url_prefix
REPO_NAME = "thesis"


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
    ThesisDraft.index.refresh()
    # Publish it
    response = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/actions/publish"
    )
    return response

#tested operations
#record communities
def _list_record_communities(client, rec_id):
    return client.get(f'{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities')
def _add_community_to_record(client, comm_id, rec_id):
    community_input = {
        "communities": [
            {"id": comm_id}
        ]
    }
    return client.post(f'{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities', json=community_input)

def _add_community_to_draft(client, comm_id, rec_id):
    community_input = {
        "communities": [
            {"id": comm_id}
        ]
    }
    return client.post(f'{RECORD_COMMUNITIES_BASE_URL}{rec_id}/draft/communities', json=community_input)

def _delete_community_from_record(client, comm_id, rec_id):
    community_input = {
        "communities": [
            {"id": comm_id}
        ]
    }
    return client.delete(f'{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities', json=community_input)

#community_records
def _list_records_by_community(client, comm_id):
    return client.get(f"/communities/{comm_id}/records")

def _remove_record_from_community(client, comm_id, rec_id):
    community_input = {
        "records": [
            {"id": rec_id},
        ]
    }
    return client.delete(f"/communities/{comm_id}/records", json=community_input)
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

def test_owner(
    client,
    community_owner,
    input_data,
    community_with_permission_cf_factory,
    search_clear,
):
    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    owner_client = community_owner.login(client)
    record_resp = _create_and_publish(
        owner_client, input_data, community_1
    )
    assert record_resp.status_code == 202
    rec_id = record_resp.json["id"]

    resp_add_comm = _add_community_to_record(client, "comm2", rec_id)
    resp_listing = _list_record_communities(client, rec_id)
    resp_delete_community = _delete_community_from_record(client, "comm2", rec_id)
    resp_listing2 = _list_record_communities(client, rec_id)

    resp_list_records_by_community = _list_records_by_community(client, "comm1")
    resp_remove_record = _remove_record_from_community(client, "comm1", rec_id)
    resp_list_records_by_community2 = _list_records_by_community(client, "comm1")

    assert resp_add_comm.status_code == 200
    assert len(resp_listing.json['hits']['hits']) == 2
    assert resp_delete_community == 200
    assert len(resp_listing2.json['hits']['hits']) == 1

    assert len(resp_list_records_by_community.json['hits']['hits']) == 1
    assert resp_remove_record.status_code == 200
    assert len(resp_list_records_by_community2.json['hits']['hits']) == 0

    #test standard crud
    rec_id = _create_and_publish(
        owner_client, input_data, community_1
    ).json["id"]
    resp_list = owner_client.get(RECORD_COMMUNITIES_BASE_URL)
    assert len(resp_list.json['hits']['hits']) == 1
    resp_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200
    resp_delete = owner_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_delete.status_code == 204
    resp_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 410



def test_reader(
    client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    input_data,
    inviter,
    search_clear,
):
    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter(community_reader.id, community_1.data["id"], "reader")
    inviter(community_reader.id, community_2.data["id"], "reader")
    owner_client = community_owner.login(client)
    record_resp = _create_and_publish(
        owner_client, input_data, community_1
    )
    assert record_resp.status_code == 202
    rec_id = record_resp.json["id"]
    community_owner.logout(client)
    reader_client = community_reader.login(client)
    # todo response code when only some additions are successful
    resp_add_comm = _add_community_to_record(reader_client, "comm2", rec_id)
    resp_listing = _list_record_communities(reader_client, rec_id)
    resp_delete_community = _delete_community_from_record(reader_client, "comm2", rec_id)
    resp_listing2 = _list_record_communities(reader_client, rec_id)

    resp_list_records_by_community = _list_records_by_community(reader_client, "comm1")
    resp_remove_record = _remove_record_from_community(reader_client, "comm1", rec_id)
    resp_list_records_by_community2 = _list_records_by_community(reader_client, "comm1")

    assert resp_add_comm.status_code == 200
    assert len(resp_listing.json['hits']['hits']) == 2
    assert resp_delete_community == 400
    assert len(resp_listing2.json['hits']['hits']) == 2

    assert len(resp_list_records_by_community.json['hits']['hits']) == 1
    assert resp_remove_record.status_code == 403
    assert len(resp_list_records_by_community2.json['hits']['hits']) == 1

    #test standard crud
    community_reader.logout(client)
    owner_client = community_owner.login(client)
    rec_id = _create_and_publish(
        owner_client, input_data, community_1
    ).json["id"]
    community_owner.logout(client)
    reader_client = community_reader.login(client)
    resp_list = reader_client.get(RECORD_COMMUNITIES_BASE_URL)
    assert len(resp_list.json['hits']['hits']) == 1
    resp_read = reader_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200
    resp_delete = reader_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_delete.status_code == 403
    resp_read = reader_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200

def test_codes_and_errors():
    """"""

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
