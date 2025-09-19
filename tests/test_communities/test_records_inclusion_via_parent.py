#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
def test_create_record_in_community_via_parent(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post("/thesis/", json={"parent": {"communities": {"default": community.id}}})
    assert response.json["parent"]["communities"]["ids"] == [community.id]
    assert response.json["parent"]["communities"]["default"] == community.id

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [community.id]
    assert response_record.json["parent"]["communities"]["default"] == community.id
