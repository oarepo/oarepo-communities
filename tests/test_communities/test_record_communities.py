import pytest
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError

from oarepo_communities.services.errors import RecordCommunityMissing
from tests.test_communities.test_community_requests import (
    _accept_request,
    _submit_request,
)
from tests.test_communities.utils import published_record_in_community


def test_include(
    logged_client,
    community_owner,
    community_with_workflow_factory,
    record_communities_service,
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
    logged_client,
    community_owner,
    community_with_workflow_factory,
    record_communities_service,
    record_service,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_owner)
    community_4 = community_with_workflow_factory("comm4", community_owner)

    response = owner_client.post(f"/communities/{community_1.id}/thesis", json={})
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
    logged_client,
    community_owner,
    community_with_workflow_factory,
    record_communities_service,
    record_service,
    request_data_factory,
    search_clear,
):
    owner_client = logged_client(community_owner)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    community_3 = community_with_workflow_factory("comm3", community_owner)

    draft_in_community = owner_client.post(
        f"/communities/{community_1.id}/thesis", json={}
    )
    draft_id = draft_in_community.json["id"]
    draft_search = owner_client.get(f"/thesis/{draft_id}/communities")
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

    draft2_in_community = owner_client.post(
        f"/communities/{community_1.id}/thesis", json={}
    )
    draft2_id = draft2_in_community.json["id"]
    # add draft to secondary community
    submit = _submit_request(
        owner_client,
        community_2.id,
        "thesis_draft",
        draft2_id,
        "secondary_community_submission",
        request_data_factory,
        payload={"community": str(community_2.id)},
    )
    accept = _accept_request(
        owner_client,
        is_draft=True,
        type="secondary_community_submission",
        record_id=draft2_id,
    )
    draft_search = owner_client.get(f"/thesis/{draft_id}/communities")
    draft2_search = owner_client.get(f"/thesis/{draft2_id}/communities")
    assert len(draft_search.json["hits"]["hits"]) == 1
    assert len(draft2_search.json["hits"]["hits"]) == 2

    published_record_ui_serialization = owner_client.get(
        f"/thesis/{published_record['id']}/communities",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )

    print()
