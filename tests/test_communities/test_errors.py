
def test_community_doesnt_exist(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response1 = owner_client.post(f"/communities/lefegfsaedf/thesis", json={})
    response2 = owner_client.post(f"/thesis/", json={"parent":{"communities": {"default": "lefegfsaedf"}}})
    assert response1.status_code == 400
    assert response2.status_code == 400

def test_community_not_specified(
    logged_client,
    community_owner,
    community,
    search_clear,
):
    owner_client = logged_client(community_owner)

    response = owner_client.post(f"/thesis/", json={})
    assert response.status_code == 400