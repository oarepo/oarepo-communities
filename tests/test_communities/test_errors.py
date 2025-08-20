#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
def test_community_doesnt_exist(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response1 = owner_client.post("/communities/lefegfsaedf/thesis", json={})
    response2 = owner_client.post("/thesis/", json={"parent": {"communities": {"default": "lefegfsaedf"}}})
    assert response1.status_code == 400
    assert response2.status_code == 400


def test_community_not_specified(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post("/thesis/", json={})
    assert response.status_code == 400
