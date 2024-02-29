import pytest
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError

from oarepo_communities.services.errors import RecordCommunityMissing
from tests.test_communities.utils import published_record_in_community


def test_include(
    client_factory,
    community_owner,
    community_with_permission_cf_factory,
    record_communities_service,
    record_service,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    community_3 = community_with_permission_cf_factory("comm3", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/records", json={})

    record_id = response.json["id"]
    record = record_service.read_draft(system_identity, record_id)._obj

    record_communities_service.include(record, community_2.id)

    record_after_include = record_service.read_draft(system_identity, record_id)._obj
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_1.id

    record_communities_service.include(record, community_3.id, default=True)
    record_after_include = record_service.read_draft(system_identity, record_id)._obj
    assert set(record_after_include.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
        community_3.id,
    }
    assert record_after_include.parent["communities"]["default"] == community_3.id


def test_remove(
    client_factory,
    community_owner,
    community_with_permission_cf_factory,
    record_communities_service,
    record_service,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory("comm2", community_owner)
    community_3 = community_with_permission_cf_factory("comm3", community_owner)
    community_4 = community_with_permission_cf_factory("comm4", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/records", json={})
    record_id = response.json["id"]
    record = record_service.read_draft(system_identity, record_id)._obj

    record_communities_service.include(record, community_2.id)
    record_communities_service.include(record, community_3.id)

    record_after_include = record_service.read_draft(system_identity, record_id)._obj
    with pytest.raises(PIDDoesNotExistError):
        record_communities_service.remove(record, "3514564")
    with pytest.raises(RecordCommunityMissing):
        record_communities_service.remove(record, "comm4")
    record_communities_service.remove(record, community_3.id)
    record_after_remove1 = record_service.read_draft(system_identity, record_id)._obj
    record_communities_service.remove(record, "comm2")
    record_after_remove2 = record_service.read_draft(system_identity, record_id)._obj

    assert set(record_after_remove1.parent["communities"]["ids"]) == {
        community_1.id,
        community_2.id,
    }
    assert set(record_after_remove2.parent["communities"]["ids"]) == {community_1.id}


def test_search(
    client_factory,
    community_owner,
    community_with_permission_cf_factory,
    record_communities_service,
    record_service,
    search_clear,
):
    owner_client = community_owner.login(client_factory())

    community_1 = community_with_permission_cf_factory("comm1", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/records", json={})
    record_id = response.json["id"]
    draft_search = owner_client.get(f"/thesis/{record_id}/communities")
    assert len(draft_search.json["hits"]["hits"]) == 1
    assert draft_search.json["hits"]["hits"][0]["id"] == community_1.id

    published_record = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )
    published_record_search = owner_client.get(
        f"/thesis/{published_record['id']}/communities"
    )
    assert len(published_record_search.json["hits"]["hits"]) == 1
    assert published_record_search.json["hits"]["hits"][0]["id"] == community_1.id
