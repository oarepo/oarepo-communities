import time

import pytest
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_users_resources.proxies import current_users_service
from tests.test_communities.utils import link2testclient


def test_disabled_endpoints(
    logged_client,
    community_owner,
    community_with_workflow_factory,
    published_record_with_community_factory,
    record_service,
    default_record_with_workflow_json,
    search_clear,
):

    owner_client = logged_client(community_owner)
    # create should work only through community
    create = owner_client.post("/thesis/", json=default_record_with_workflow_json)
    assert create.status_code == 400

    community_1 = community_with_workflow_factory("comm1", community_owner)
    draft = owner_client.post(
        f"/communities/{community_1.id}/thesis", json=default_record_with_workflow_json
    ).json
    published_record = published_record_with_community_factory(owner_client, community_1.id)

    publish = owner_client.post(f"/thesis/{draft['id']}/draft/actions/publish")
    delete = owner_client.delete(f"/thesis/{published_record.json['id']}")
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


def test_default_community_workflow_changed(
    logged_client,
    community_owner,
    users,
    community_with_workflow_factory,
    inviter,
    set_community_workflow,
    service_config,
    draft_with_community_factory,
    search_clear,
):
    community_reader = users[0]
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory(
        "comm2",
        community_owner,
    )
    inviter(community_reader, community_1.id, "reader")
    inviter(community_reader, community_2.id, "reader")

    record1 = draft_with_community_factory(owner_client, community_1.id)
    record2 = draft_with_community_factory(owner_client, community_2.id)
    record4 = draft_with_community_factory(reader_client, community_1.id)

    request_should_be_allowed = owner_client.post(
        f"/thesis/{record1.json['id']}/draft/requests/publish_draft"
    )
    submit = owner_client.post(
        link2testclient(request_should_be_allowed.json["links"]["actions"]["submit"])
    )
    accept_should_be_denied = reader_client.post(
        link2testclient(submit.json["links"]["actions"]["accept"])
    )
    accept = owner_client.post(
        link2testclient(submit.json["links"]["actions"]["accept"])
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
    record5 = draft_with_community_factory(owner_client, community_1.id)
    request_should_be_forbidden = owner_client.post(
        f"/thesis/{record5.json['id']}/draft/requests/publish_draft"
    )
    assert request_should_still_work.status_code == 201
    assert request_should_be_forbidden.status_code == 403


from invenio_communities.generators import CommunityRoleNeed
from invenio_records_resources.services.errors import PermissionDeniedError


def test_can_possibly_create_in_community(
    community_owner,
    users,
    community_with_workflow_factory,
    inviter,
    service_config,
    record_service,
    search_clear,
):
    # tries to .. in with one community with default workflow allowing reader and owner, than adds another community
    # allowing curator, which should allow curator to deposit too
    community_curator = users[0]
    rando_user = users[1]
    community_1 = community_with_workflow_factory("comm1", community_owner)
    inviter(community_curator, community_1.id, "curator")
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
    inviter(community_curator, community_2.id, "curator")
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


def test_record_owners_in_default_record_community_needs(
    community_owner,
    users,
    logged_client,
    community_with_workflow_factory,
    inviter,
    remover,
    draft_with_community_factory,
    service_config,
    record_service,
    search_clear,
):
    # tries to .. in with one community with default workflow allowing reader and owner, than adds another community
    # allowing curator, which should allow curator to deposit too
    community_curator = users[0]
    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    inviter(community_curator, community_1.id, "curator")
    inviter(community_curator, community_2.id, "curator")

    curator_client = logged_client(community_curator)
    record1 = draft_with_community_factory(
        curator_client,
        community_1.id,
        custom_workflow="record_owner_in_default_record_community",
    )
    record2 = draft_with_community_factory(
        curator_client,
        community_2.id,
        custom_workflow="record_owner_in_default_record_community",
    )

    read_before = curator_client.get(f"/thesis/{record1.json['id']}/draft?expand=true")
    search_before = curator_client.get(f"/user/thesis/")
    type_ids = {
        request_type["type_id"]
        for request_type in read_before.json["expanded"]["request_types"]
    }
    assert "publish_draft" in type_ids
    assert len(search_before.json["hits"]["hits"]) == 2

    remover(
        community_curator.id, community_1.id
    )  # the curator now isn't in community and should not be able to create
    # publish request on the record nor search it

    read_after = curator_client.get(f"/thesis/{record1.json['id']}/draft?expand=true")
    assert read_after.status_code == 403
    search_after = curator_client.get(f"/user/thesis/")
    assert len(search_after.json["hits"]["hits"]) == 1


def test_record_owners_in_record_community_needs(
    community_owner,
    users,
    logged_client,
    community_with_workflow_factory,
    community_inclusion_service,
    draft_with_community_factory,
    inviter,
    remover,
    service_config,
    record_service,
    search_clear,
):
    # user's record should not be available after getting kicked out of the community of the record
    community_curator = users[0]
    community_1 = community_with_workflow_factory("comm1", community_owner)
    community_2 = community_with_workflow_factory("comm2", community_owner)
    inviter(community_curator, community_1.id, "curator")
    inviter(community_curator, community_2.id, "curator")
    community_curator.identity.provides.add(
        CommunityRoleNeed(community_1.id, "curator")
    )

    curator_client = logged_client(community_curator)

    record1 = draft_with_community_factory(
        curator_client,
        community_1.id,
        custom_workflow="record_owner_in_record_community",
    )
    record2 = draft_with_community_factory(
        curator_client,
        community_2.id,
        custom_workflow="record_owner_in_record_community",
    )

    read_before1 = curator_client.get(f"/thesis/{record1.json['id']}/draft?expand=true")
    read_before2 = curator_client.get(f"/thesis/{record2.json['id']}/draft?expand=true")
    search_before = curator_client.get(f"/user/thesis/")

    remover(community_curator.id, community_2.id)
    read_after1 = curator_client.get(f"/thesis/{record1.json['id']}/draft?expand=true")
    read_after2 = curator_client.get(f"/thesis/{record2.json['id']}/draft?expand=true")
    search_after = curator_client.get(f"/user/thesis/")

    assert read_before1.status_code == 200
    assert read_before2.status_code == 200
    assert read_after1.status_code == 200
    assert read_after2.status_code == 403
    assert len(search_before.json["hits"]["hits"]) == 2
    assert len(search_after.json["hits"]["hits"]) == 1