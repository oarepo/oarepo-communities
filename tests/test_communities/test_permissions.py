import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from thesis.records.api import ThesisDraft, ThesisRecord

from tests.test_communities.utils import (
    _create_record_in_community,
    link_api2testclient,
    published_record_in_community,
)


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
    # todo error handling
    try:
        create = owner_client.post("/thesis/", json={})
    except TypeError:
        pass
    # assert create.status_code == 403

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





@pytest.fixture()
def service_config():
    from thesis.services.records.config import ThesisServiceConfig

    return ThesisServiceConfig


@pytest.fixture()
def requests_service():
    # from invenio_requests.services.requests.service import RequestsService
    from invenio_requests.proxies import current_requests_service

    return current_requests_service


def test_scenarios(
    init_cf,
    logged_client,
    community_owner,
    community_reader,
    community_with_permission_cf_factory,
    patch_requests_permissions,
    inviter,
    set_community_scenario,
    service_config,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_permission_cf_factory("comm1", community_owner)
    community_2 = community_with_permission_cf_factory(
        "comm2",
        community_owner,
    )
    inviter("2", community_1.id, "reader")
    inviter("2", community_2.id, "reader")

    set_community_scenario("default", str(community_1.id))
    set_community_scenario("default", str(community_2.id))

    record1 = _create_record_in_community(owner_client, community_1.id)
    record2 = _create_record_in_community(owner_client, community_2.id)
    record3 = _create_record_in_community(owner_client, community_1.id)
    record4 = _create_record_in_community(reader_client, community_1.id)

    request_should_be_allowed = owner_client.post(
        f"/thesis/{record1.json['id']}/draft/requests/thesis_publish_draft"
    )
    submit = owner_client.post(
        link_api2testclient(
            request_should_be_allowed.json["links"]["actions"]["submit"]
        )
    )
    accept_should_be_denied = reader_client.post(
        link_api2testclient(submit.json["links"]["actions"]["accept"])
    )
    accept = owner_client.post(
        link_api2testclient(submit.json["links"]["actions"]["accept"])
    )
    assert accept_should_be_denied.status_code == 403
    assert request_should_be_allowed.status_code == 201

    # old permissions should not allow this for reader, but reader is in editors so it should be fine with new ones
    update_draft = reader_client.put(
        f"/thesis/{record4.json['id']}/draft",
        json=record4.json | {"metadata": {"title": "should do"}},
    )
    assert update_draft.status_code == 200
    assert update_draft.json["metadata"]["title"] == "should do"

    set_community_scenario("wawawa", str(community_2.id))

    request_should_be_forbidden = owner_client.post(
        f"/thesis/{record2.json['id']}/draft/requests/thesis_publish_draft"
    )
    assert request_should_be_forbidden.status_code == 403

    # check changing of the scenario
    set_community_scenario("wawawa", str(community_1.id))
    request_should_be_forbidden = owner_client.post(
        f"/thesis/{record3.json['id']}/draft/requests/thesis_publish_draft"
    )
    assert request_should_be_forbidden.status_code == 403

    # record status in json?
    record1 = owner_client.get(f"/thesis/{record1.json['id']}?expand=True")

    print()
