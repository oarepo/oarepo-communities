
def test_create_record_in_community_via_parent(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(f"/thesis", json={
        "parent": {
            "communities": {
                "default": community.id
            }
        }
    })
    assert response.json["parent"]["communities"]["ids"] == [community.id]
    assert response.json["parent"]["communities"]["default"] == community.id

    response_record = owner_client.get(f"/thesis/{response.json['id']}/draft")
    assert response_record.json["parent"]["communities"]["ids"] == [community.id]
    assert response_record.json["parent"]["communities"]["default"] == community.id
