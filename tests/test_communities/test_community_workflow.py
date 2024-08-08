from invenio_communities.communities.records.api import Community


def test_change_workflow(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    result = owner_client.put(
        f"/communities/{community.id}",
        json=community.data | {"custom_fields": {"workflow": "doesnotexist"}},
    )
    assert result.status_code == 400
    result = owner_client.put(
        f"/communities/{community.id}",
        json=community.data | {"custom_fields": {"workflow": "custom"}},
    )
    assert result.status_code == 200
    community_id = str(community.id)
    record = Community.get_record(community_id)
    assert record.custom_fields["workflow"] == "custom"
