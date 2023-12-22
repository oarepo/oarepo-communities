import copy

import pytest

from thesis.records.api import ThesisDraft, ThesisRecord
from thesis.resources.record_communities.config import (
    ThesisRecordCommunitiesResourceConfig,
)
from invenio_requests.proxies import current_requests_service

RECORD_COMMUNITIES_BASE_URL = ThesisRecordCommunitiesResourceConfig.url_prefix
REPO_NAME = "thesis"

from invenio_requests.records.api import Request

def link_api2testclient(api_link):
    base_string = 'https://127.0.0.1:5000/api/'
    return api_link[len(base_string)-1:]


def create_publish_in_community(client, input_data, community):
    """Create a draft and publish it."""
    # Create the draft
    response = _create_record_in_community(client, input_data, community.id)
    recid = response.json["id"]

    # Publish it
    response = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/actions/publish"
    )
    return response


# tested operations
# record communities
def _list_record_communities(client, rec_id):
    return client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities")


def _add_community_to_record(client, comm_id, rec_id):
    community_input = {"communities": [{"id": comm_id}]}
    return client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities", json=community_input
    )


def _add_community_to_draft(client, comm_id, rec_id):
    community_input = {"communities": [{"id": comm_id}]}
    return client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}/draft/communities", json=community_input
    )


def _delete_community_from_record(client, comm_id, rec_id):
    community_input = {"communities": [{"id": comm_id}]}
    return client.delete(
        f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}/communities", json=community_input
    )


# community_records
def _create_record_in_community(client, input_data, comm_id):
    return client.post(f"/communities/{comm_id}/records", json=input_data)
def _list_records_by_community(client, comm_id):
    return client.get(f"/communities/{comm_id}/records")

def _list_drafts_by_community(client, comm_id):
    return client.get(f"/communities/{comm_id}/draft/records")

def _request_base_lifecycle(creator_client, receiver_client, receiver, record, community, community_submission_data_func, **extra_kwargs):
    community_submission_data = community_submission_data_func(community, record, **extra_kwargs)
    submission_create = creator_client.post("/requests/create", json=community_submission_data)
    submission_submit = creator_client.post(link_api2testclient(submission_create.json['links']['actions']['submit']))
    # todo - link should be on the record
    request = current_requests_service.read(receiver.identity, submission_submit.json['id'])
    accept_link = link_api2testclient(request.links["actions"]["accept"])
    receiver_response = receiver_client.post(accept_link)
    return submission_create, submission_submit, receiver_response

def _check_community_submission_and_publish(submission_create, submission_submit, receiver_response,
                                            submission_create_code=201, submission_submit_code=200, receiver_response_code=200):
    assert submission_create.status_code == submission_create_code
    assert submission_submit.status_code == submission_submit_code
    assert receiver_response.status_code == receiver_response_code




def _remove_record_from_community(client, comm_id, rec_id):
    community_input = {
        "records": [
            {"id": rec_id},
        ]
    }
    return client.delete(f"/communities/{comm_id}/records", json=community_input)


def _init_env(
        client_factory,
        community_owner,
        community_reader,
        community_curator,
        community_with_permission_cf_factory,
        inviter):

    reader_client = community_reader.login(client_factory())
    owner_client = community_owner.login(client_factory())
    curator_client = community_curator.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter(community_reader.id, community_1.data["id"], "reader")
    inviter(community_reader.id, community_2.data["id"], "reader")

    return reader_client, owner_client, curator_client, community_1, community_2

def test_cf(
    client,
    community_owner,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    community_owner.login(client)
    record_resp = create_publish_in_community(client, input_data, community_with_permissions_cf)
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

    draft_with_community = _create_record_in_community(client, input_data, "comm1")

    assert draft_with_community.status_code == 201
    assert draft_with_community.json["parent"]["communities"]["ids"] == [community_1.id]
    assert draft_with_community.json["parent"]["communities"]["default"] == community_1.id

    record_resp = create_publish_in_community(owner_client, input_data, community_1)
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
    assert len(resp_listing.json["hits"]["hits"]) == 2
    assert resp_delete_community == 200
    assert len(resp_listing2.json["hits"]["hits"]) == 1

    assert len(resp_list_records_by_community.json["hits"]["hits"]) == 1
    assert resp_remove_record.status_code == 200
    assert len(resp_list_records_by_community2.json["hits"]["hits"]) == 0

    # test standard crud
    rec_id = create_publish_in_community(owner_client, input_data, community_1).json["id"]
    ThesisRecord.index.refresh()
    resp_list = owner_client.get(RECORD_COMMUNITIES_BASE_URL)
    assert len(resp_list.json["hits"]["hits"]) == 2
    resp_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200
    resp_delete = owner_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_delete.status_code == 204
    resp_read = owner_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 410

@pytest.fixture
def client_factory(app):
    def _client_factory():
        with app.test_client() as client:
            return client
    return _client_factory

def test_reader(
    client,
    client_factory,
    community_owner,
    community_reader,
    community_curator,
    community_with_permission_cf_factory,
    input_data,
    inviter,
    request_data_factory,
    search_clear,
):
    reader_client = community_reader.login(client_factory())
    owner_client = community_owner.login(client_factory())
    curator_client = community_curator.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter(community_reader.id, community_1.data["id"], "reader")
    inviter(community_reader.id, community_2.data["id"], "reader")

    create_reader = _create_record_in_community(reader_client, input_data, "comm1")
    assert create_reader.status_code == 403
    record_resp = create_publish_in_community(owner_client, input_data, community_1)
    assert record_resp.status_code == 202
    rec_id = record_resp.json["id"]

    inviter(community_curator.id, community_2.data["id"], "curator")
    resp_reader = _request_base_lifecycle(reader_client, reader_client, community_owner, record_resp.json, community_2.data["id"], request_data_factory)
    resp_curator = _request_base_lifecycle(reader_client, curator_client, community_curator, record_resp.json,
                                           community_2.data["id"], request_data_factory)
    _check_community_submission_and_publish(*resp_reader, receiver_response_code=403)
    _check_community_submission_and_publish(*resp_curator)
    record = owner_client.get(f"/thesis/{rec_id}")
    assert len(record.json["parent"]["communities"]["ids"]) == 2

    draft_with_community = _create_record_in_community(client, input_data, "comm1")
    assert draft_with_community.status_code == 403 # test permission


    # todo response code when only some additions are successful
    #resp_add_comm = _add_community_to_record(reader_client, "comm2", rec_id)
    resp_listing = _list_record_communities(reader_client, rec_id)
    resp_delete_community = _delete_community_from_record(
        reader_client, "comm2", rec_id
    )
    resp_listing2 = _list_record_communities(reader_client, rec_id)

    resp_list_records_by_community = _list_records_by_community(reader_client, "comm1")
    resp_remove_record = _remove_record_from_community(reader_client, "comm1", rec_id)
    resp_list_records_by_community2 = _list_records_by_community(reader_client, "comm1")

    #assert resp_add_comm.status_code == 200
    assert len(resp_listing.json["hits"]["hits"]) == 2
    assert resp_delete_community == 400
    assert len(resp_listing2.json["hits"]["hits"]) == 2

    assert len(resp_list_records_by_community.json["hits"]["hits"]) == 1
    assert resp_remove_record.status_code == 403
    assert len(resp_list_records_by_community2.json["hits"]["hits"]) == 1

    # test standard crud
    #community_reader.logout(client)
    #owner_client = community_owner.login(client)
    rec_id = create_publish_in_community(owner_client, input_data, community_1).json["id"]
    #community_owner.logout(client)
    #reader_client = community_reader.login(client)
    resp_list = reader_client.get(RECORD_COMMUNITIES_BASE_URL)
    assert len(resp_list.json["hits"]["hits"]) == 1
    resp_read = reader_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200
    resp_delete = reader_client.delete(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_delete.status_code == 403
    resp_read = reader_client.get(f"{RECORD_COMMUNITIES_BASE_URL}{rec_id}")
    assert resp_read.status_code == 200


def test_codes_and_errors(client_factory,
    community_owner,
    community_reader,
    community_curator,
    community_with_permission_cf_factory,
    input_data,
    inviter,
    request_data_factory,
    search_clear,):

    reader_client, owner_client, curator_client, community_1, community_2 = _init_env(client_factory,
    community_owner,
    community_reader,
    community_curator,
    community_with_permission_cf_factory,
    inviter)

    record_resp = create_publish_in_community(owner_client, input_data, community_1)

    resp = _request_base_lifecycle(reader_client, owner_client, community_owner,
                                                record_resp.json, community_1.data["id"], request_data_factory)
    print()




def test_migrate(
    client_factory,
    community_owner,
    community_reader,
    community_curator,
    community_with_permission_cf_factory,
    input_data,
    inviter,
    request_data_factory,
    search_clear,):

    reader_client, owner_client, curator_client, community_1, community_2 = _init_env(client_factory,
    community_owner,
    community_reader,
    community_curator,
    community_with_permission_cf_factory,
    inviter)

    record_resp = create_publish_in_community(owner_client, input_data, community_1)

    creator = {"oarepo_community": community_1.data["id"]}
    type = "community-migration"
    payload = {"community": community_1.data["id"]}
    migrate_responses = _request_base_lifecycle(reader_client, owner_client, community_owner,
                                                record_resp.json, community_2.data["id"], request_data_factory,
                                                type=type, payload=payload)
    assert record_resp.json["parent"]["communities"]["default"] == community_1.data["id"]
    assert record_resp.json["parent"]["communities"]["ids"] == [community_1.data["id"]]
    _check_community_submission_and_publish(*migrate_responses)
    ThesisRecord.index.refresh()
    record_reload = owner_client.get(f"/thesis/{record_resp.json['id']}")
    assert record_reload.json["parent"]["communities"]["default"] == community_2.data["id"]
    assert record_reload.json["parent"]["communities"]["ids"] == [community_2.data["id"]]










def test_rando(
    client,
    rando_user,
    community_with_permissions_cf,
    input_data,
    search_clear,
):
    rando_client = rando_user.login(client)
    record_resp = create_publish_in_community(
        rando_client, input_data, community_with_permissions_cf
    )
    assert record_resp.status_code == 403
