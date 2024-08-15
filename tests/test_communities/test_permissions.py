import pytest
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities

from tests.test_communities.utils import (
    _create_record_in_community,
    link_api2testclient,
    published_record_in_community,
)


def test_disabled_endpoints(
    logged_client,
    community_owner,
    community_with_workflow_factory,
    record_service,
    default_workflow_json,
    search_clear,
):

    owner_client = logged_client(community_owner)
    # create should work only through community
    create = owner_client.post("/thesis/", json=default_workflow_json)
    assert create.status_code == 400

    community_1 = community_with_workflow_factory("comm1", community_owner)
    draft = owner_client.post(
        f"/communities/{community_1.id}/thesis", json=default_workflow_json
    ).json
    published_record = published_record_in_community(
        owner_client, community_1.id, record_service, community_owner
    )

    publish = owner_client.post(f"/thesis/{draft['id']}/draft/actions/publish")
    delete = owner_client.delete(f"/thesis/{published_record['id']}")
    assert publish.status_code == 403
    assert delete.status_code == 403


@pytest.fixture()
def service_config():
    from thesis.services.records.config import ThesisServiceConfig

    return ThesisServiceConfig


@pytest.fixture()
def requests_service():
    # from invenio_requests.services.requests.service import RequestsService
    from invenio_requests.proxies import current_requests_service

    return current_requests_service


def test_scenario_change(
    logged_client,
    community_owner,
    community_reader,
    community_with_workflow_factory,
    inviter,
    set_community_workflow,
    service_config,
    patch_requests_permissions,
    search_clear,
):
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory(
        "comm2",
        community_owner,
    )
    inviter("2", community_1.id, "reader")
    inviter("2", community_2.id, "reader")

    record1 = _create_record_in_community(owner_client, community_1.id)
    record2 = _create_record_in_community(owner_client, community_2.id)
    record4 = _create_record_in_community(reader_client, community_1.id)

    request_should_be_allowed = owner_client.post(
        f"/thesis/{record1.json['id']}/draft/requests/publish_draft"
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

    set_community_workflow(str(community_1.id), "no")
    record = Community.get_record(str(community_1.id))
    assert record.custom_fields["workflow"] == "no"
    request_should_still_work = owner_client.post(
        f"/thesis/{record2.json['id']}/draft/requests/publish_draft"
    )
    # todo add workflow to marshmallow
    record5 = _create_record_in_community(owner_client, community_1.id)
    request_should_be_forbidden = owner_client.post(
        f"/thesis/{record5.json['id']}/draft/requests/publish_draft"
    )
    assert request_should_still_work.status_code == 201
    assert request_should_be_forbidden.status_code == 403


from invenio_communities.generators import CommunityRoleNeed
from invenio_records_resources.services.errors import PermissionDeniedError


def test_can_possibly_create_in_community(
    community_owner,
    community_curator,
    rando_user,
    community_with_workflow_factory,
    inviter,
    service_config,
    record_service,
    search_clear,
):
    # tries to .. in with one community with default workflow allowing reader and owner, than adds another community
    # allowing curator, which should allow curator to deposit too
    community_1 = community_with_workflow_factory("comm1", community_owner)
    inviter(community_curator.id, community_1.id, "curator")
    community_curator.identity.provides.add(
        CommunityRoleNeed(community_1.id, "curator")
    )
    record_service.require_permission(community_owner.identity, "view_deposit_page")
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(
            community_curator.identity, "view_deposit_page"
        )
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(rando_user.identity, "view_deposit_page")

    community_2 = community_with_workflow_factory(
        "comm2",
        community_owner,
    )
    current_communities.service.update(
        community_owner.identity,
        id_=community_2.id,
        data=community_2.data | {"custom_fields": {"workflow": "custom"}},
    )
    inviter(community_curator.id, community_2.id, "curator")
    community_curator.identity.provides.add(
        CommunityRoleNeed(community_2.id, "curator")
    )
    community2read = current_communities.service.read(
        community_curator.identity, community_2.id
    )
    assert community2read.data["custom_fields"]["workflow"] == "custom"
    Community.index.refresh()

    # test goes over all workflows and communities; curator can now create in community 2 that allows create for cura
    record_service.require_permission(community_owner.identity, "view_deposit_page")
    record_service.require_permission(community_curator.identity, "view_deposit_page")
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(rando_user.identity, "view_deposit_page")
