#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the reopen-on-close behaviour of community-submission requests.

When a community-submission review is declined, cancelled or expired, the custom
actions in ``oarepo_communities.requests.community_submission`` replace the closed
request with a fresh open one on the same community. The draft therefore returns
to the ``draft_with_review`` state (community still selected, submit-for-review
available) instead of ending up ``declined``/``expired`` or losing the community.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_access.permissions import system_identity

if TYPE_CHECKING:
    from typing import Any


def _create_and_submit_review(
    community_id: str, submitter_client: Any, communities_model: Any, upload_file: Any
) -> tuple[str, str]:
    """Create a draft, open a community-submission review and submit it.

    Mirrors ``_test_review_process`` from ``test_community_records`` and returns
    the draft id together with the review request id.
    """
    resp = submitter_client.post(
        "/records",
        json={
            "$schema": "local://communities_test-v1.0.0.json",
            "files": {"enabled": False},
            "metadata": {
                "contributors": ["Contributor 1"],
                "creators": ["Creator 1", "Creator 2"],
                "title": "blabla",
            },
        },
    )
    assert resp.status_code == 201
    id_ = resp.json["id"]
    upload_file(
        identity=submitter_client.user_fixture.identity,
        record_id=id_,
        files_service=communities_model.proxies.current_service.draft_files,
    )
    review = submitter_client.put(
        f"/records/{id_}/draft/review",
        json={"receiver": {"community": community_id}, "type": "community-submission"},
    )
    assert review.status_code == 200
    submit = submitter_client.post(f"/records/{id_}/draft/actions/submit-review")
    assert submit.status_code == 202
    return id_, review.json["id"]


def _assert_reopened_and_resubmittable(
    submitter_client: Any,
    id_: str,
    old_review_id: str,
    community_id: str,
) -> None:
    """Assert the shared reopen outcome, identical for decline/cancel/expire.

    The draft is back in ``draft_with_review`` on a fresh open review for the same
    community, the review is attributed to the original submitter (not whoever
    closed the previous one), and the submitter can submit it for review again.
    """
    old_review = submitter_client.get(f"/requests/{old_review_id}").json

    draft = submitter_client.get(f"/records/{id_}/draft").json
    assert draft["status"] == "draft_with_review"
    assert "submit-review" in draft["links"]

    new_review = draft["parent"]["review"]
    assert new_review["id"] != old_review_id
    assert new_review["status"] == "created"
    assert new_review["type"] == "community-submission"
    assert new_review["receiver"]["community"] == community_id

    # The reopened request keeps the original submitter as creator. The embedded
    # ``parent.review`` only carries id/type/receiver/status, so read the full
    # request to compare creators.
    reopened = submitter_client.get(f"/requests/{new_review['id']}").json
    assert reopened["created_by"] == old_review["created_by"]

    # The submitter can submit the reopened review again.
    resubmit = submitter_client.post(f"/records/{id_}/draft/actions/submit-review")
    assert resubmit.status_code == 202


def test_community_submission_decline_reopens_review(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    upload_file,
    search_clear,
):
    """Declining a submission reopens a fresh review so it can be resubmitted."""
    community_id = str(community.id)
    community_reader = users[0]
    invite(community_reader, community_id, "reader")
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    id_, review_id = _create_and_submit_review(community_id, reader_client, communities_model, upload_file)

    # The reviewer (community owner) declines the submission.
    decline = owner_client.post(f"/requests/{review_id}/actions/decline")
    assert decline.status_code == 200

    # The original request is kept and recorded as declined (history preserved).
    assert owner_client.get(f"/requests/{review_id}").json["status"] == "declined"

    _assert_reopened_and_resubmittable(reader_client, id_, review_id, community_id)


def test_community_submission_cancel_reopens_review(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    invite,
    upload_file,
    search_clear,
):
    """Cancelling a submission reopens a fresh review so it can be resubmitted."""
    community_id = str(community.id)
    community_reader = users[0]
    invite(community_reader, community_id, "reader")
    reader_client = logged_client(community_reader)

    id_, review_id = _create_and_submit_review(community_id, reader_client, communities_model, upload_file)

    # The submitter cancels their own submission.
    cancel = reader_client.post(f"/requests/{review_id}/actions/cancel")
    assert cancel.status_code == 200

    # The original request is kept and recorded as cancelled (history preserved).
    assert reader_client.get(f"/requests/{review_id}").json["status"] == "cancelled"

    _assert_reopened_and_resubmittable(reader_client, id_, review_id, community_id)


def test_community_submission_expire_reopens_review(
    logged_client,
    community_owner,
    users,
    community,
    communities_model,
    requests_service,
    invite,
    upload_file,
    search_clear,
):
    """Expiring a submission reopens a fresh review so it can be resubmitted.

    Expire has no user-facing action link (it is triggered by the system), so it
    is exercised through the requests service as ``system_identity``.
    """
    community_id = str(community.id)
    community_reader = users[0]
    invite(community_reader, community_id, "reader")
    reader_client = logged_client(community_reader)

    id_, review_id = _create_and_submit_review(community_id, reader_client, communities_model, upload_file)

    # Expire the submission (system action).
    requests_service.execute_action(system_identity, review_id, "expire")

    # The original request is kept and recorded as expired (history preserved).
    assert reader_client.get(f"/requests/{review_id}").json["status"] == "expired"

    _assert_reopened_and_resubmittable(reader_client, id_, review_id, community_id)
