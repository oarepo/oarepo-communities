# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations


def test_community_doesnt_exist(
    logged_client,
    community_owner,
    community,
    communities_model,
    urls,
    search_clear,
):
    owner_client = logged_client(community_owner)
    response2 = owner_client.post(urls["BASE_URL"], json={"parent": {"communities": {"default": "lefegfsaedf"}}})
    assert response2.status_code == 400
