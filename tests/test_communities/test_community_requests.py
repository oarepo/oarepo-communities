#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import pytest
from pytest_oarepo.communities.functions import invite
from pytest_oarepo.requests.functions import get_request_type
from thesis.records.api import ThesisRecord

from oarepo_communities.errors import (
    CommunityAlreadyIncludedException,
    CommunityNotIncludedException,
    PrimaryCommunityException,
)


def _accept_request(
    receiver_client,
    type,
    record_id,
    link2testclient,
    is_draft=False,
    no_accept_link=False,
    **kwargs,
):
    if is_draft:
        record_after_submit = receiver_client.get(f"/thesis/{record_id}/draft?expand=true")
    else:
        record_after_submit = receiver_client.get(f"/thesis/{record_id}?expand=true")

    request_dict = {}
    for request in record_after_submit.json["expanded"]["requests"]:
        if request["type"] == type:
            request_dict = request
    assert request_dict

    if no_accept_link:
        assert "accept" not in request_dict["links"]["actions"]
        return None
    accept_link = link2testclient(request_dict["links"]["actions"]["accept"])
    receiver_response = receiver_client.post(accept_link)
    return receiver_response


def _init_env(
    logged_client,
    community_get_or_create,
    community_owner,
    community_reader,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, community_1.data["id"], "reader")
    invite(community_reader, community_2.data["id"], "reader")

    return reader_client, owner_client, community_1, community_2


def test_community_publish(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_factory,
    submit_request_on_draft,
    link2testclient,
    search_clear,
):
    community_reader = users[0]
    invite(community_reader, community.id, "reader")
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record = draft_with_community_factory(community_reader.identity, community.id)
    record_id = record["id"]
    submit = submit_request_on_draft(community_reader.identity, record_id, "publish_draft")
    _accept_request(
        reader_client,
        type="publish_draft",
        record_id=record_id,
        link2testclient=link2testclient,
        is_draft=True,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client,
        type="publish_draft",
        record_id=record_id,
        link2testclient=link2testclient,
        is_draft=True,
    )  # owner can

    resp_draft = owner_client.get(f"/thesis/{record_id}/draft")
    resp_record = owner_client.get(f"/thesis/{record_id}")

    # record was published
    assert resp_draft.status_code == 404
    assert resp_record.status_code == 200


def test_community_delete(
    logged_client,
    community_owner,
    users,
    community,
    published_record_with_community_factory,
    submit_request_on_record,
    link2testclient,
    test_vocabularies,
    search_clear,
):
    community_reader = users[0]
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)
    invite(community_reader, community.id, "reader")
    record = published_record_with_community_factory(community_reader.identity, community.id)
    record_id = record["id"]

    submit = submit_request_on_record(
        community_reader.identity,
        record_id,
        "delete_published_record",
        create_additional_data={"payload": {"removal_reason": "duplicate"}},
    )
    _accept_request(
        reader_client,
        type="delete_published_record",
        record_id=record_id,
        link2testclient=link2testclient,
        no_accept_link=True,
    )  # reader can't accept the request
    accept_owner = _accept_request(
        owner_client,
        type="delete_published_record",
        record_id=record_id,
        link2testclient=link2testclient,
    )  # owner can

    ThesisRecord.index.refresh()
    resp_record = owner_client.get(f"/thesis/{record_id}")
    resp_search = owner_client.get("/thesis/")

    # record was published
    assert resp_record.status_code == 410
    assert len(resp_search.json["hits"]["hits"]) == 0


def test_community_migration(
    logged_client,
    community_owner,
    users,
    community_get_or_create,
    published_record_with_community_factory,
    submit_request_on_record,
    link2testclient,
    search_clear,
):
    community_reader = users[0]
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_get_or_create,
        community_owner,
        community_reader,
    )

    record = published_record_with_community_factory(community_reader.identity, community_1.id)
    record_id = record["id"]
    record_before = reader_client.get(f"/thesis/{record_id}")
    submit = submit_request_on_record(
        community_reader.identity,
        record_id,
        "initiate_community_migration",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    _accept_request(
        reader_client,
        type="initiate_community_migration",
        record_id=record_id,
        link2testclient=link2testclient,
        no_accept_link=True,
    )  # reader can accept the request
    accept_initiate_request_owner = _accept_request(
        owner_client,
        type="initiate_community_migration",
        record_id=record_id,
        link2testclient=link2testclient,
    )  # confirm should be created and submitted automatically
    accept_confirm_request_owner = _accept_request(
        owner_client,
        type="confirm_community_migration",
        record_id=record_id,
        link2testclient=link2testclient,
    )
    record_after = owner_client.get(f"/thesis/{record_id}?expand=true")
    assert record_before.json["parent"]["communities"]["default"] == community_1.data["id"]
    assert record_before.json["parent"]["communities"]["ids"] == [community_1.data["id"]]

    assert record_after.json["parent"]["communities"]["default"] == community_2.data["id"]
    assert record_after.json["parent"]["communities"]["ids"] == [community_2.data["id"]]


def test_community_submission_secondary(
    logged_client,
    community_owner,
    users,
    community_get_or_create,
    published_record_with_community_factory,
    create_request_on_record,
    submit_request_on_record,
    link2testclient,
    search_clear,
):
    community_reader = users[0]
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_get_or_create,
        community_owner,
        community_reader,
    )
    record = published_record_with_community_factory(community_reader.identity, community_1.id)
    record_id = record["id"]

    record_before = owner_client.get(f"/thesis/{record_id}")
    with pytest.raises(CommunityAlreadyIncludedException):
        create_request_on_record(
            community_reader.identity,
            record_id,
            "secondary_community_submission",
            additional_data={"payload": {"community": str(community_1.id)}},
        )
    submit = submit_request_on_record(
        community_reader.identity,
        record_id,
        "secondary_community_submission",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    _accept_request(
        reader_client,
        type="secondary_community_submission",
        record_id=record_id,
        link2testclient=link2testclient,
        no_accept_link=True,
    )  # reader can accept the request
    accept_owner = _accept_request(
        owner_client,
        type="secondary_community_submission",
        record_id=record_id,
        link2testclient=link2testclient,
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
    users,
    community_get_or_create,
    published_record_with_community_factory,
    create_request_on_record,
    submit_request_on_record,
    link2testclient,
    search_clear,
):
    community_reader = users[0]
    reader_client, owner_client, community_1, community_2 = _init_env(
        logged_client,
        community_get_or_create,
        community_owner,
        community_reader,
    )

    record = published_record_with_community_factory(community_reader.identity, community_1.id)
    record_id = record["id"]

    submit_request_on_record(
        community_reader.identity,
        record_id,
        "secondary_community_submission",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    accept_owner = _accept_request(
        owner_client,
        type="secondary_community_submission",
        record_id=record_id,
        link2testclient=link2testclient,
    )

    record_before = owner_client.get(f"/thesis/{record_id}")

    # TODO this should not work - it should not produce a link
    with pytest.raises(PrimaryCommunityException):
        create_request_on_record(
            community_reader.identity,
            record_id,
            "remove_secondary_community",
            additional_data={"payload": {"community": str(community_1.id)}},
        )

    submit_request_on_record(
        community_reader.identity,
        record_id,
        "remove_secondary_community",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    _accept_request(
        reader_client,
        type="remove_secondary_community",
        record_id=record_id,
        link2testclient=link2testclient,
        no_accept_link=True,
    )  # reader can't accept the request
    accept_owner = _accept_request(
        owner_client,
        type="remove_secondary_community",
        record_id=record_id,
        link2testclient=link2testclient,
    )  # owner can

    record_after = owner_client.get(f"/thesis/{record_id}")
    assert set(record_before.json["parent"]["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert set(record_after.json["parent"]["communities"]["ids"]) == {community_1.id}

    # assert link is not present
    applicable_requests = reader_client.get(link2testclient(record["links"]["applicable-requests"])).json["hits"][
        "hits"
    ]
    assert get_request_type(applicable_requests, "remove_secondary_community") is None
    with pytest.raises(CommunityNotIncludedException):
        reader_client.post(
            f"/thesis/{record_id}/requests/remove_secondary_community",
            json={"payload": {"community": str(community_2.id)}},
        )


def test_community_role_ui_serialization(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_factory,
    submit_request_on_draft,
    ui_serialized_community_role,
    search_clear,
):
    community_reader = users[0]
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)
    invite(community_reader, community.id, "reader")
    record = draft_with_community_factory(community_reader.identity, community.id)
    record_id = record["id"]

    submit = submit_request_on_draft(community_reader.identity, record_id, "publish_draft")

    def compare_result(result):
        assert result.items() >= ui_serialized_community_role(community.id).items()
        assert (
            result["links"].items()
            >= {
                "self": f"https://127.0.0.1:5000/api/communities/{community.id}",
                "self_html": "https://127.0.0.1:5000/communities/public",
            }.items()
        )

    request = owner_client.get(
        f"/requests/extended/{submit['id']}",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )

    compare_result(request.json["receiver"])

    request_list = owner_client.get(
        "/requests/",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )

    compare_result(request_list.json["hits"]["hits"][0]["receiver"])


"""
def test_community_role_ui_serialization_cs(
    logged_client,
    community_owner,
    community_reader,
    community,
    request_data_factory,
    record_service,
    ui_serialized_community_role,
    clear_babel_context,
    search_clear,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record_id = _create_record_in_community(reader_client, community.id).json["id"]

    submit = _submit_request(
        reader_client,
        community.id,
        "thesis_draft",
        record_id,
        "publish_draft",
        request_data_factory,
    )
    clear_babel_context()
    request = owner_client.get(
        f"/requests/extended/{submit.json['id']}",
        headers={
            "Accept": "application/vnd.inveniordm.v1+json",
            "Accept-Language": "cs",
        },
    )
    assert (
        request.json["receiver"]["label"] == 'Role "Vlastník" komunity "My Community"'
    )
    clear_babel_context()
"""
