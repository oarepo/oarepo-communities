# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from invenio_requests.proxies import current_requests_service
from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity


def _my_request_ids(client, shared_with_me: bool = False) -> set[str]:
    current_requests_service.record_cls.index.refresh()
    response = client.get(f"/user/requests?shared_with_me={str(shared_with_me).lower()}")
    assert response.status_code == 200
    return {hit["id"] for hit in response.json["hits"]["hits"]}


def test_user_requests_include_reviews_submitted_to_own_communities(
    logged_client,
    community_owner,
    users,
    community_get_or_create_in_default_workflow,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    submitter = users[0]
    other_community_owner = users[1]
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    community_2 = community_get_or_create_in_default_workflow(other_community_owner, "comm2")
    invite(submitter, str(community_1.id), "reader")
    invite(submitter, str(community_2.id), "reader")

    draft_1 = draft_with_community_submission_factory(submitter.identity, str(community_1.id))
    draft_2 = draft_with_community_submission_factory(submitter.identity, str(community_2.id))
    review_1 = submit_review(submitter.identity, draft_1["id"])
    review_2 = submit_review(submitter.identity, draft_2["id"])

    assert _my_request_ids(logged_client(community_owner)) == {review_1["id"]}
    assert _my_request_ids(logged_client(other_community_owner)) == {review_2["id"]}
    assert _my_request_ids(logged_client(submitter)) == {review_1["id"], review_2["id"]}


def test_community_received_reviews_are_not_listed_as_shared_with_me(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """The broadened "my requests" query is negated in the shared tab, a request must not show in both."""
    submitter = users[0]
    invite(submitter, str(community.id), "reader")
    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    submit_review(submitter.identity, draft["id"])

    assert _my_request_ids(logged_client(community_owner), shared_with_me=True) == set()


def test_community_membership_does_not_reveal_requests_the_role_cannot_read(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    """Any membership broadens the filter to all community-received requests; the read permission must narrow it."""
    submitter, other_reader = users[0], users[1]
    invite(submitter, str(community.id), "reader")
    invite(other_reader, str(community.id), "reader")
    draft = draft_with_community_submission_factory(submitter.identity, str(community.id))
    submit_review(submitter.identity, draft["id"])

    assert _my_request_ids(logged_client(other_reader)) == set()


def test_user_requests_include_requests_received_by_own_group(
    logged_client,
    community_owner,
    users,
    community,
    published_record_with_community_factory,
    create_request_on_record,
    requests_service,
    roles,
    add_user_in_role,
    invite,
    search_clear,
):
    submitter, group_member = users[0], users[1]
    group = roles[0]
    add_user_in_role(group_member, group)
    invite(submitter, str(community.id), "reader")
    record = published_record_with_community_factory(submitter.identity, str(community.id))

    request = create_request_on_record(
        submitter.identity,
        record["id"],
        "delete_published_record",
        additional_data={"payload": {"removal_reason": "duplicate"}},
        receiver=group,
    )
    requests_service.execute_action(submitter.identity, id_=request["id"], action="submit")

    assert request["receiver"] == {"group": group.id}
    assert _my_request_ids(logged_client(group_member)) == {request["id"]}


def test_user_requests_include_requests_received_by_any_of_multiple_entities(
    logged_client,
    users,
    community,
    published_record_with_community_factory,
    create_request_on_record,
    requests_service,
    roles,
    add_user_in_role,
    invite,
    search_clear,
):
    """The multiple receiver's reference matches nobody; each entity is reached through its own indexed grant."""
    submitter, receiving_user, group_member = users[0], users[1], users[2]
    group = roles[0]
    add_user_in_role(group_member, group)
    invite(submitter, str(community.id), "reader")
    record = published_record_with_community_factory(submitter.identity, str(community.id))
    receiver = {"multiple": MultipleEntitiesEntity.create_id([{"user": str(receiving_user.id)}, {"group": group.id}])}

    request = create_request_on_record(
        submitter.identity,
        record["id"],
        "delete_published_record",
        additional_data={"payload": {"removal_reason": "duplicate"}},
        receiver=receiver,
    )
    requests_service.execute_action(submitter.identity, id_=request["id"], action="submit")

    assert request["receiver"] == receiver
    assert _my_request_ids(logged_client(receiving_user)) == {request["id"]}
    assert _my_request_ids(logged_client(group_member)) == {request["id"]}


def test_user_requests_include_requests_received_by_own_community_role(
    logged_client,
    community_owner,
    users,
    community,
    published_record_with_community_factory,
    submit_request_on_record,
    invite,
    search_clear,
):
    submitter = users[0]
    invite(submitter, str(community.id), "reader")
    record = published_record_with_community_factory(submitter.identity, str(community.id))

    request = submit_request_on_record(
        submitter.identity,
        record["id"],
        "delete_published_record",
        create_additional_data={"payload": {"removal_reason": "duplicate"}},
    )

    owner_client = logged_client(community_owner)

    assert request["receiver"] == {"community_role": f"{community.id}:owner"}
    assert owner_client.get(f"/requests/{request['id']}").status_code == 200
    assert request["id"] in _my_request_ids(owner_client)
