#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import pytest
from invenio_access.permissions import system_identity
from oarepo_runtime.typing import record_from_result

from oarepo_communities.errors import CommunityNotIncludedException


def test_include(
    logged_client,
    community_owner,
    community_inclusion_service,
    record_service,
    community_get_or_create,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, slug="comm1")
    community_2 = community_get_or_create(community_owner, slug="comm2")
    community_3 = community_get_or_create(community_owner, slug="comm3")

    response = owner_client.post(f"/communities/{community_1.id}/thesis", json={})

    record_id = response.json["id"]
    record = record_from_result(record_service.read_draft(system_identity, record_id))

    community_inclusion_service.include(record, community_2.id, record_service=record_service)

    record_after_include = record_from_result(record_service.read_draft(system_identity, record_id))
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_1.id

    community_inclusion_service.include(record, community_3.id, default=True, record_service=record_service)
    record_after_include = record_from_result(record_service.read_draft(system_identity, record_id))
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
        community_3.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_3.id


def test_remove(
    logged_client,
    community_owner,
    community_inclusion_service,
    record_service,
    community_get_or_create,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")

    response = owner_client.post(f"/communities/{community_1.id}/thesis", json={})
    record_id = response.json["id"]
    record = record_from_result(record_service.read_draft(system_identity, record_id))
    community_inclusion_service.include(record, community_2.id, record_service=record_service)
    record_after_include = record_from_result(record_service.read_draft(system_identity, record_id))

    with pytest.raises(CommunityNotIncludedException):
        community_inclusion_service.remove(
            record,
            "ef916d1b-9f2b-4444-849e-1a905b7c3b5d",
            record_service=record_service,
        )
    community_inclusion_service.remove(record, community_2.id, record_service=record_service)
    record_after_remove = record_from_result(record_service.read_draft(system_identity, record_id))

    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert set(record_after_remove.parent["communities"]["ids"]) == {community_1.id}
