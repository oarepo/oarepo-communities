import pytest
from invenio_access.permissions import system_identity

from oarepo_communities.errors import CommunityNotIncludedException


def test_include(
    logged_client,
    community_owner,
    community_with_workflow_factory,
    community_inclusion_service,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/thesis", json={})

    record_id = response.json["id"]
    record = record_service.read_draft(system_identity, record_id)._obj

    community_inclusion_service.include(
        record, community_2.id, record_service=record_service
    )

    record_after_include = record_service.read_draft(system_identity, record_id)._obj
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_1.id

    community_inclusion_service.include(
        record, community_3.id, default=True, record_service=record_service
    )
    record_after_include = record_service.read_draft(
        system_identity, record_id, record_service=record_service
    )._obj
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
        community_3.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_3.id


def test_remove(
    logged_client,
    community_owner,
    community_with_workflow_factory,
    community_inclusion_service,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/thesis", json={})
    record_id = response.json["id"]
    record = record_service.read_draft(system_identity, record_id)._obj
    community_inclusion_service.include(
        record, community_2.id, record_service=record_service
    )
    record_after_include = record_service.read_draft(system_identity, record_id)._obj

    with pytest.raises(CommunityNotIncludedException):
        community_inclusion_service.remove(
            record,
            "ef916d1b-9f2b-4444-849e-1a905b7c3b5d",
            record_service=record_service,
        )
    community_inclusion_service.remove(
        record, community_2.id, record_service=record_service
    )
    record_after_remove = record_service.read_draft(system_identity, record_id)._obj

    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert set(record_after_remove.parent["communities"]["ids"]) == {community_1.id}
