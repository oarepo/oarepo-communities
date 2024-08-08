from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_communities.communities.records.api import Community


def test_change_workflow(
    logged_client,
    community_owner,
    community_with_default_workflow,
    search_clear,
):
    owner_client = logged_client(community_owner)

    result = owner_client.put(
        f"/communities/{community_with_default_workflow.id}", json=community_with_default_workflow.data | {"custom_fields": {"workflow": "doesnotexist"}}
    )
    assert result.status_code == 400
    result = owner_client.put(
        f"/communities/{community_with_default_workflow.id}", json=community_with_default_workflow.data | {"custom_fields": {"workflow": "custom"}}
    )
    assert result.status_code == 200
    community_id = str(community_with_default_workflow.id)
    record = Community.get_record(community_id)
    assert record.custom_fields["workflow"] == "custom"
