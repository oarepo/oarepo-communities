# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Workflow state transitions of a draft going through the community submission review."""

from __future__ import annotations

import pytest


@pytest.fixture
def review_transitions_community(community_owner, community_get_or_create):
    return community_get_or_create(
        community_owner,
        slug="review-transitions",
        workflow="review_transitions",
        allowed_workflows=["review_transitions"],
    )


def test_submitting_review_applies_submitted_transition(
    logged_client,
    users,
    review_transitions_community,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    urls,
    search_clear,
):
    submitter = users[0]
    invite(submitter, str(review_transitions_community.id), "reader")
    submitter_client = logged_client(submitter)

    draft = draft_with_community_submission_factory(submitter.identity, str(review_transitions_community.id))
    assert draft["state"] == "draft"

    submit_review(submitter.identity, draft["id"])

    assert submitter_client.get(f"{urls['BASE_URL']}/{draft['id']}/draft").json["state"] == "submitted"


@pytest.mark.parametrize(
    ("action", "actor", "expected_state"),
    [
        ("decline", "community_owner", "declined"),
        ("cancel", "submitter", "cancelled"),
    ],
)
def test_closing_review_applies_its_transition(
    logged_client,
    community_owner,
    users,
    review_transitions_community,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    urls,
    search_clear,
    action,
    actor,
    expected_state,
):
    submitter = users[0]
    invite(submitter, str(review_transitions_community.id), "reader")
    submitter_client = logged_client(submitter)
    actor_client = logged_client({"community_owner": community_owner, "submitter": submitter}[actor])

    draft = draft_with_community_submission_factory(submitter.identity, str(review_transitions_community.id))
    review = submit_review(submitter.identity, draft["id"])

    response = actor_client.post(f"{urls['BASE_URL_REQUESTS']}/{review['id']}/actions/{action}")
    assert response.status_code == 200

    assert submitter_client.get(f"{urls['BASE_URL']}/{draft['id']}/draft").json["state"] == expected_state


def test_accepting_review_applies_accepted_transition(
    logged_client,
    community_owner,
    users,
    review_transitions_community,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    urls,
    search_clear,
):
    submitter = users[0]
    invite(submitter, str(review_transitions_community.id), "reader")
    submitter_client = logged_client(submitter)
    owner_client = logged_client(community_owner)

    draft = draft_with_community_submission_factory(submitter.identity, str(review_transitions_community.id))
    review = submit_review(submitter.identity, draft["id"])

    response = owner_client.post(f"{urls['BASE_URL_REQUESTS']}/{review['id']}/actions/accept")
    assert response.status_code == 200

    assert submitter_client.get(f"{urls['BASE_URL']}/{draft['id']}").json["state"] == "accepted"
