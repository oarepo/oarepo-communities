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

import pytest
from pytest_oarepo.requests.functions import get_request_type

from oarepo_communities.errors import CommunityAlreadyIncludedError


@pytest.fixture
def accept_request(urls, link2testclient):
    def _accept_request(
        receiver_client,
        type_,
        record_id,
        is_draft=False,
        no_accept_link=False,
        **kwargs: Any,
    ) -> Any:
        if is_draft:
            record_after_submit = receiver_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")
        else:
            record_after_submit = receiver_client.get(f"{urls['BASE_URL']}/{record_id}?expand=true")

        request_dict = {}
        for request in record_after_submit.json["expanded"]["requests"]:
            if request["type"] == type_:
                request_dict = request
        assert request_dict

        if no_accept_link:
            assert "accept" not in request_dict["links"]["actions"]
            return None
        accept_link = link2testclient(request_dict["links"]["actions"]["accept"])
        return receiver_client.post(accept_link)

    return _accept_request


@pytest.fixture
def env(
    logged_client,
    users,
    community_get_or_create,
    community_owner,
    invite,
) -> tuple:
    community_reader = users[0]
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, str(community_1.id), "reader")
    invite(community_reader, str(community_2.id), "reader")

    return reader_client, owner_client, community_1, community_2


def test_community_publish(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_factory,
    submit_request_on_draft,
    communities_model,
    accept_request,
    invite,
    urls,
    search_clear,
):
    community_reader = users[0]
    invite(community_reader, str(community.id), "reader")
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record = draft_with_community_factory(community_reader.identity, str(community.id))
    record_id = record["id"]
    submit_request_on_draft(community_reader.identity, record_id, "publish_draft")
    accept_request(
        reader_client,
        type_="publish_draft",
        record_id=record_id,
        is_draft=True,
        no_accept_link=True,
    )  # reader can accept the request
    accept_request(
        owner_client,
        type_="publish_draft",
        record_id=record_id,
        is_draft=True,
    )  # owner can

    resp_draft = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft")
    resp_record = owner_client.get(f"{urls['BASE_URL']}/{record_id}")

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
    urls,
    # TODO: delete request reason validation
    # test_vocabularies,
    communities_model,
    invite,
    accept_request,
    search_clear,
):
    community_reader = users[0]
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)
    invite(community_reader, str(community.id), "reader")
    record = published_record_with_community_factory(community_reader.identity, str(community.id))
    record_id = record["id"]

    submit_request_on_record(
        community_reader.identity,
        record_id,
        "delete_published_record",
        create_additional_data={"payload": {"removal_reason": "duplicate"}},
    )
    accept_request(
        reader_client,
        type_="delete_published_record",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can't accept the request
    accept_request(
        owner_client,
        type_="delete_published_record",
        record_id=record_id,
    )  # owner can
    communities_model.Record.index.refresh()
    resp_record = owner_client.get(f"{urls['BASE_URL']}/{record_id}")
    resp_search = owner_client.get(urls["BASE_URL"])

    # record was published
    assert resp_record.status_code == 410
    assert len(resp_search.json["hits"]["hits"]) == 0


def test_community_migration(
    published_record_with_community_factory,
    submit_request_on_record,
    urls,
    env,
    accept_request,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = (
        env[0],
        env[1],
        env[2],
        env[3],
    )

    record = published_record_with_community_factory(reader_client.user_fixture.identity, str(community_1.id))
    record_id = record["id"]
    record_before = reader_client.get(f"{urls['BASE_URL']}/{record_id}")
    submit_request_on_record(
        reader_client.user_fixture.identity,
        record_id,
        "initiate_community_migration",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    accept_request(
        reader_client,
        type_="initiate_community_migration",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_request(
        owner_client,
        type_="initiate_community_migration",
        record_id=record_id,
    )  # confirm should be created and submitted automatically
    accept_request(
        owner_client,
        type_="confirm_community_migration",
        record_id=record_id,
    )
    record_after = owner_client.get(f"{urls['BASE_URL']}/{record_id}?expand=true")
    assert record_before.json["parent"]["communities"]["default"] == str(community_1.id)
    assert record_before.json["parent"]["communities"]["ids"] == [str(community_1.id)]

    assert record_after.json["parent"]["communities"]["default"] == str(community_2.id)
    assert record_after.json["parent"]["communities"]["ids"] == [str(community_2.id)]


def test_community_submission_secondary(
    published_record_with_community_factory,
    create_request_on_record,
    submit_request_on_record,
    urls,
    env,
    accept_request,
    link2testclient,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = (
        env[0],
        env[1],
        env[2],
        env[3],
    )
    record = published_record_with_community_factory(reader_client.user_fixture.identity, str(community_1.id))
    record_id = record["id"]

    record_before = owner_client.get(f"{urls['BASE_URL']}/{record_id}")
    with pytest.raises(CommunityAlreadyIncludedError):
        create_request_on_record(
            reader_client.user_fixture.identity,
            record_id,
            "secondary_community_submission",
            additional_data={"payload": {"community": str(community_1.id)}},
        )
    submit_request_on_record(
        reader_client.user_fixture.identity,
        record_id,
        "secondary_community_submission",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    accept_request(
        reader_client,
        type_="secondary_community_submission",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can accept the request
    accept_request(
        owner_client,
        type_="secondary_community_submission",
        record_id=record_id,
    )  # owner can
    record_after = owner_client.get(f"{urls['BASE_URL']}/{record_id}")

    assert record_before.json["parent"]["communities"]["default"] == str(community_1.id)
    assert record_after.json["parent"]["communities"]["default"] == str(community_1.id)
    assert set(record_before.json["parent"]["communities"]["ids"]) == {str(community_1.id)}
    assert set(record_after.json["parent"]["communities"]["ids"]) == {
        str(community_1.id),
        str(community_2.id),
    }


def test_remove_secondary(
    published_record_with_community_factory,
    create_request_on_record,
    submit_request_on_record,
    link2testclient,
    urls,
    env,
    accept_request,
    search_clear,
):
    reader_client, owner_client, community_1, community_2 = (
        env[0],
        env[1],
        env[2],
        env[3],
    )

    record = published_record_with_community_factory(reader_client.user_fixture.identity, str(community_1.id))
    record_id = record["id"]

    submit_request_on_record(
        reader_client.user_fixture.identity,
        record_id,
        "secondary_community_submission",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    accept_request(
        owner_client,
        type_="secondary_community_submission",
        record_id=record_id,
    )

    record_before = owner_client.get(f"{urls['BASE_URL']}/{record_id}")
    reader_client.get(link2testclient(record_before.json["links"]["applicable-requests"])).json["hits"]

    # TODO: this should not work - it should not produce a link
    # i'm not sure i get this - eg if i call applicable-requests, i can't know which community is to be removed
    """
    with pytest.raises(PrimaryCommunityException):
        create_request_on_record(
            community_reader.identity,
            record_id,
            "remove_secondary_community",
            additional_data={"payload": {"community": str(community_1.id)}},
        )
    """

    submit_request_on_record(
        reader_client.user_fixture.identity,
        record_id,
        "remove_secondary_community",
        create_additional_data={"payload": {"community": str(community_2.id)}},
    )
    accept_request(
        reader_client,
        type_="remove_secondary_community",
        record_id=record_id,
        no_accept_link=True,
    )  # reader can't accept the request
    accept_request(
        owner_client,
        type_="remove_secondary_community",
        record_id=record_id,
    )  # owner can

    record_after = owner_client.get(f"{urls['BASE_URL']}/{record_id}")
    assert set(record_before.json["parent"]["communities"]["ids"]) == {
        str(community_1.id),
        str(community_2.id),
    }
    assert set(record_after.json["parent"]["communities"]["ids"]) == {str(community_1.id)}

    # assert link is not present
    applicable_requests = reader_client.get(link2testclient(record["links"]["applicable-requests"])).json["hits"][
        "hits"
    ]
    assert get_request_type(applicable_requests, "remove_secondary_community") is None


@pytest.mark.skip
def test_community_role_ui_serialization(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_factory,
    submit_request_on_draft,
    ui_serialized_community_role,
    invite,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)
    invite(community_reader, str(community.id), "reader")
    record = draft_with_community_factory(community_reader.identity, str(community.id))
    record_id = record["id"]

    submit = submit_request_on_draft(community_reader.identity, record_id, "publish_draft")

    def compare_result(result) -> None:
        assert result.items() >= ui_serialized_community_role(str(community.id)).items()
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
