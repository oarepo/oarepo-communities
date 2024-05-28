import pytest
from invenio_records_resources.services.errors import PermissionDeniedError
from thesis.records.api import ThesisDraft, ThesisRecord

from tests.test_communities.utils import published_record_in_community


def test_receiver_permissions_community_role_perm_undefined(
    requests_service,
    community_with_permissions_cf,
    create_publish_request,
    community_owner,
    community_curator,
    search_clear,
):
    publish_request = create_publish_request(
        identity=community_owner.identity,
        receiver={"community": community_with_permissions_cf.id},
    )
    requests_service.execute_action(
        identity=community_owner.identity, id_=publish_request.id, action="submit"
    )

    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(
            identity=community_curator.identity, id_=publish_request.id, action="accept"
        )


def test_disabled_endpoints(
    init_cf,
    logged_client,
    community_owner,
    community_with_permission_cf_factory,
    record_service,
    search_clear,
):

    owner_client = logged_client(community_owner)

    # create should work only through community
    create = owner_client.post("/thesis/", json={})
    assert create.status_code == 403

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    draft = owner_client.post(
        f"/communities/{community_1.id}/thesis/records", json={}
    ).json
    published_record = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )

    publish = owner_client.post(f"/thesis/{draft['id']}/draft/actions/publish")
    delete = owner_client.delete(f"/thesis/{published_record['id']}")
    assert publish.status_code == 403
    assert delete.status_code == 403


def test_community_allows_every_authenticated_user(
    init_cf,
    logged_client,
    community_owner,
    rando_user,
    community_with_permission_cf_factory,
    community_permissions_cf_authenticated_user_read,
    record_service,
    search_clear,
):
    from oarepo_communities.cache import allowed_communities_cache

    allowed_communities_cache.cache_clear()
    owner_client = logged_client(community_owner)
    user_client = logged_client(rando_user)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory(
        "comm2",
        community_owner,
        community_permissions_cf_custom=community_permissions_cf_authenticated_user_read,
    )

    record1 = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )
    record2 = published_record_in_community(
        owner_client, community_2.id, record_service, community_owner
    )

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    response_record1 = user_client.get(f"/thesis/{record1['id']}")
    response_record2 = user_client.get(f"/thesis/{record2['id']}")

    assert response_record1.status_code == 403
    assert response_record2.status_code == 200

    search1 = user_client.get(f"/communities/{community_1.id}/records")
    search2 = user_client.get(f"/communities/{community_2.id}/records")
    search_model = user_client.get("/thesis/")

    assert len(search1.json["hits"]["hits"]) == 0
    assert len(search2.json["hits"]["hits"]) == 1
    assert len(search_model.json["hits"]["hits"]) == 1
