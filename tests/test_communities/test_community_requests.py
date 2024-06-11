import pytest
from thesis.resources.record_communities.config import (
    ThesisRecordCommunitiesResourceConfig,
)

from oarepo_communities.errors import (
    CommunityAlreadyIncludedException,
    CommunityNotIncludedException,
    PrimaryCommunityException,
)
from tests.test_communities.utils import (
    _create_record_in_community,
    published_record_in_community,
)

RECORD_COMMUNITIES_BASE_URL = ThesisRecordCommunitiesResourceConfig.url_prefix
REPO_NAME = "thesis"


def link_api2testclient(api_link):
    base_string = "https://127.0.0.1:5000/api/"
    return api_link[len(base_string) - 1 :]


def find_request_by_type(requests, type):
    for request in requests:
        if request["type"] == type:
            return request
    return None


def _create_request(
    creator_client,
    community_id,
    record_type,
    record_id,
    request_type,
    request_data_func,
    **kwargs,
):
    request_data = request_data_func(
        community_id, record_type, record_id, request_type, **kwargs
    )
    create_response = creator_client.post("/requests/", json=request_data)
    return create_response


def _submit_request(
    creator_client,
    community_id,
    record_type,
    record_id,
    request_type,
    request_data_func,
    **kwargs,
):
    create_response = _create_request(
        creator_client,
        community_id,
        record_type,
        record_id,
        request_type,
        request_data_func,
        **kwargs,
    )

    submit_response = creator_client.post(
        link_api2testclient(create_response.json["links"]["actions"]["submit"])
    )
    return submit_response


def _accept_request(
    receiver_client,
    type,
    record_id,
    is_draft=False,
    no_accept_link=False,
    **kwargs,
):
    if is_draft:
        record_after_submit = receiver_client.get(
            f"/thesis/{record_id}/draft?expand=true"
        )
    else:
        record_after_submit = receiver_client.get(f"/thesis/{record_id}?expand=true")
    request_dict = find_request_by_type(record_after_submit.json["requests"], type)
    if no_accept_link:
        assert "accept" not in request_dict["links"]["actions"]
        return None
    accept_link = link_api2testclient(request_dict["links"]["actions"]["accept"])
    receiver_response = receiver_client.post(accept_link)
    return receiver_response


def _init_env(
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    inviter,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    inviter(community_reader.id, community_1.data["id"], "reader")
    inviter(community_reader.id, community_2.data["id"], "reader")

    return reader_client, owner_client, community_1, community_2


def test_community_publish(
    logged_client,
    community_owner,
    community_reader,
    community_with_default_workflow,
    request_data_factory,
    record_service,
    patch_requests_permissions,
    search_clear,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record_id = _create_record_in_community(
        reader_client, community_with_default_workflow.id
    ).json["id"]
    submit = _submit_request(
        reader_client,
        community_with_default_workflow.id,
        "thesis_draft",
        record_id,
        "thesis_publish_draft",
        request_data_factory,
    )
    _accept_request(
        reader_client,
        type="thesis_publish_draft",
        record_id=record_id,
        is_draft=True,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client, type="thesis_publish_draft", record_id=record_id, is_draft=True
    )  # owner can

    resp_draft = owner_client.get(f"/thesis/{record_id}/draft")
    resp_record = owner_client.get(f"/thesis/{record_id}")

    # record was published
    assert resp_draft.status_code == 404
    assert resp_record.status_code == 200


def test_community_delete(
    logged_client,
    community_owner,
    community_reader,
    community_with_default_workflow,
    request_data_factory,
    record_service,
    patch_requests_permissions,
    search_clear,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record_id = published_record_in_community(
        owner_client,
        community_with_default_workflow.id,
        record_service,
        community_owner,
    )["id"]

    submit = _submit_request(
        reader_client,
        community_with_default_workflow.id,
        "thesis",
        record_id,
        "thesis_delete_record",
        request_data_factory,
    )
    _accept_request(
        reader_client,
        type="thesis_delete_record",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client, type="thesis_delete_record", record_id=record_id
    )  # owner can

    resp_record = owner_client.get(f"/thesis/{record_id}")
    resp_search = owner_client.get(f"/thesis/")

    # record was published
    assert resp_record.status_code == 410
    assert len(resp_search.json["hits"]["hits"]) == 0


def test_community_migration(
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    request_data_factory,
    record_service,
    inviter,
    patch_requests_permissions,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_owner,
        community_reader,
        community_with_workflow_factory,
        inviter,
    )

    record_id = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )["id"]
    record_before = owner_client.get(f"/thesis/{record_id}")

    submit = _submit_request(
        reader_client,
        community_2.id,
        "thesis",
        record_id,
        "thesis_community_migration",
        request_data_factory,
        payload={"community": str(community_2.id)},
    )
    _accept_request(
        reader_client,
        type="thesis_community_migration",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client, type="thesis_community_migration", record_id=record_id
    )  # owner can

    record_after = owner_client.get(f"/thesis/{record_id}")

    assert (
        record_before.json["parent"]["communities"]["default"] == community_1.data["id"]
    )
    assert record_before.json["parent"]["communities"]["ids"] == [
        community_1.data["id"]
    ]

    assert (
        record_after.json["parent"]["communities"]["default"] == community_2.data["id"]
    )
    assert record_after.json["parent"]["communities"]["ids"] == [community_2.data["id"]]


def test_community_submission_secondary(
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    inviter,
    request_data_factory,
    record_service,
    patch_requests_permissions,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_owner,
        community_reader,
        community_with_workflow_factory,
        inviter,
    )
    record_id = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )["id"]

    record_before = owner_client.get(f"/thesis/{record_id}")
    with pytest.raises(CommunityAlreadyIncludedException):
        _create_request(
            reader_client,
            community_1.id,
            "thesis",
            record_id,
            "thesis_secondary_community_submission",
            request_data_factory,
            payload={"community": str(community_1.id)},
        )

    submit = _submit_request(
        reader_client,
        community_2.id,
        "thesis",
        record_id,
        "thesis_secondary_community_submission",
        request_data_factory,
        payload={"community": str(community_2.id)},
    )
    _accept_request(
        reader_client,
        type="thesis_secondary_community_submission",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client, type="thesis_secondary_community_submission", record_id=record_id
    )  # owner can
    record_after = owner_client.get(f"/thesis/{record_id}")

    assert record_before.json["parent"]["communities"]["default"] == community_1.id
    assert record_after.json["parent"]["communities"]["default"] == community_1.id
    assert set(record_before.json["parent"]["communities"]["ids"]) == {community_1.id}
    assert set(record_after.json["parent"]["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }


def test_remove_secondary(
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    inviter,
    request_data_factory,
    record_service,
    patch_requests_permissions,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_owner,
        community_reader,
        community_with_workflow_factory,
        inviter,
    )

    record_id = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )["id"]

    submit = _submit_request(
        reader_client,
        community_2.id,
        "thesis",
        record_id,
        "thesis_secondary_community_submission",
        request_data_factory,
        payload={"community": str(community_2.id)},
    )
    accept_owner = _accept_request(
        owner_client, type="thesis_secondary_community_submission", record_id=record_id
    )

    record_before = owner_client.get(f"/thesis/{record_id}")

    with pytest.raises(PrimaryCommunityException):
        _create_request(
            reader_client,
            community_1.id,
            "thesis",
            record_id,
            "thesis_remove_secondary_community",
            request_data_factory,
            payload={"community": str(community_1.id)},
        )

    submit = _submit_request(
        reader_client,
        community_2.id,
        "thesis",
        record_id,
        "thesis_remove_secondary_community",
        request_data_factory,
        payload={"community": str(community_2.id)},
    )
    _accept_request(
        reader_client,
        type="thesis_remove_secondary_community",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client, type="thesis_remove_secondary_community", record_id=record_id
    )  # owner can

    record_after = owner_client.get(f"/thesis/{record_id}")
    assert set(record_before.json["parent"]["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert set(record_after.json["parent"]["communities"]["ids"]) == {community_1.id}

    with pytest.raises(CommunityNotIncludedException):
        _create_request(
            reader_client,
            community_2.id,
            "thesis",
            record_id,
            "thesis_remove_secondary_community",
            request_data_factory,
            payload={"community": str(community_2.id)},
        )


def test_ui_serialization(
    logged_client,
    community_owner,
    community_reader,
    community_with_default_workflow,
    request_data_factory,
    record_service,
    ui_serialized_community,
    patch_requests_permissions,
    search_clear,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record_id = _create_record_in_community(
        reader_client, community_with_default_workflow.id
    ).json["id"]

    submit = _submit_request(
        reader_client,
        community_with_default_workflow.id,
        "thesis_draft",
        record_id,
        "thesis_publish_draft",
        request_data_factory,
    )

    request = owner_client.get(
        f"/requests/extended/{submit.json['id']}",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert request.json["receiver"] == ui_serialized_community(
        community_with_default_workflow.id
    )
    request_list = owner_client.get(
        "/requests/",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert request_list.json["hits"]["hits"][0]["receiver"] == ui_serialized_community(
        community_with_default_workflow.id
    )
