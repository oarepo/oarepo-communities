#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_records_resources.services.errors import PermissionDeniedError
from oarepo_rdm.oai.percolator import init_percolators
from oarepo_runtime.typing import record_from_result
from pytest_oarepo.communities.functions import invite, set_community_workflow


def test_disabled_endpoints(
    logged_client,
    community_owner,
    draft_with_community_factory,
    published_record_with_community_factory,
    default_record_with_workflow_json,
    community_get_or_create,
    record_service,
    urls,
    search_clear,
):
    owner_client = logged_client(community_owner)
    # create should work only through community
    create = owner_client.post(urls["BASE_URL"], json=default_record_with_workflow_json)
    assert create.status_code == 400
    community_1 = community_get_or_create(community_owner, "comm1")
    draft = draft_with_community_factory(community_owner.identity, str(community_1.id))
    published_record = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    publish = owner_client.post(f"{urls['BASE_URL']}/{draft['id']}/draft/actions/publish")
    delete = owner_client.delete(f"{urls['BASE_URL']}/{published_record['id']}")
    assert publish.status_code == 403
    assert delete.status_code == 403


def test_default_community_workflow_changed(
    logged_client,
    community_owner,
    users,
    community_get_or_create,
    draft_with_community_factory,
    create_request_on_draft,
    link2testclient,
    get_action_url,
    urls,
    search_clear,
):
    init_percolators()
    community_reader = users[0]
    owner_client = logged_client(community_owner)
    reader_client = logged_client(community_reader)

    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    invite(community_reader, str(community_1.id), "reader")
    invite(community_reader, str(community_2.id), "reader")

    record1 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    record2 = draft_with_community_factory(community_owner.identity, str(community_2.id))
    record4 = draft_with_community_factory(community_reader.identity, str(community_1.id))

    request_should_be_allowed = create_request_on_draft(community_owner.identity, record1["id"], "publish_draft")
    submit = owner_client.post(link2testclient(request_should_be_allowed.links["actions"]["submit"]))
    accept_should_be_denied = reader_client.post(link2testclient(submit.json["links"]["actions"]["accept"]))
    assert accept_should_be_denied.status_code == 403

    owner_client.post(link2testclient(submit.json["links"]["actions"]["accept"]))

    # old permissions should not allow this for reader, but reader is in editors so it should be fine with new ones
    update_draft = reader_client.put(
        f"{urls['BASE_URL']}/{record4['id']}/draft",
        json=record4 | {"metadata": {"title": "should do"}},
    )
    assert update_draft.status_code == 200
    assert update_draft.json["metadata"]["title"] == "should do"

    set_community_workflow(str(community_1.id), "no")
    record = Community.get_record(str(community_1.id))
    assert record.custom_fields["workflow"] == "no"
    create_request_on_draft(community_owner.identity, record2["id"], "publish_draft")
    record5 = draft_with_community_factory(community_owner.identity, str(community_1.id))
    with pytest.raises(PermissionDeniedError):
        create_request_on_draft(community_owner.identity, record5["id"], "publish_draft")


def test_can_possibly_create_in_community(
    community_owner,
    users,
    community_get_or_create,
    record_service,
    search_clear,
):
    # tries to .. in with one community with default workflow allowing reader and owner, than adds another community
    # allowing curator, which should allow curator to deposit too
    community_curator = users[0]
    rando_user = users[1]
    community_1 = community_get_or_create(community_owner, "comm1")
    invite(community_curator, str(community_1.id), "curator")
    record_service.require_permission(community_owner.identity, "view_deposit_page")
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(community_curator.identity, "view_deposit_page")
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(rando_user.identity, "view_deposit_page")

    community_2 = community_get_or_create(community_owner, "comm2")
    set_community_workflow(str(community_2.id), "custom")
    invite(community_curator, str(community_2.id), "curator")
    community2read = current_communities.service.read(community_curator.identity, str(community_2.id))
    assert community2read.data["custom_fields"]["workflow"] == "custom"
    Community.index.refresh()

    # test goes over all workflows and communities; curator can now create in community 2 that allows create for cura
    record_service.require_permission(community_owner.identity, "view_deposit_page")
    record_service.require_permission(community_curator.identity, "view_deposit_page")
    with pytest.raises(PermissionDeniedError):
        record_service.require_permission(rando_user.identity, "view_deposit_page")


def _record_owners_in_record_community_test(
    community_owner,
    users,
    logged_client,
    draft_with_community_factory,
    record_service,
    community_get_or_create,
    workflow,
    urls,
    results,
) -> None:
    # tries to read record when user in record's primary community, in noth primary and secondary, in secondary and
    # in none
    community_curator = users[0]
    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    community_3 = community_get_or_create(community_curator, "comm3")

    owner_client = logged_client(community_owner)

    record = draft_with_community_factory(
        community_owner.identity,
        str(community_1.id),
        custom_workflow=workflow,
    )
    record_id = record["id"]

    read_com1 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.add(community_2, default=False)
    record.parent.commit()

    read_com2 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.remove(community_1)
    record.parent.communities.add(community_3, default=True)
    record.parent.commit()

    read_com3 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.remove(community_2)
    record.parent.commit()

    read_com4 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    assert read_com1.status_code == results[0]
    assert read_com2.status_code == results[1]
    assert read_com3.status_code == results[2]
    assert read_com4.status_code == results[3]


def test_record_owners_in_record_community_needs(
    community_owner,
    urls,
    users,
    logged_client,
    community_get_or_create,
    draft_with_community_factory,
    record_service,
    search_clear,
) -> None:
    _record_owners_in_record_community_test(
        community_owner,
        users,
        logged_client,
        draft_with_community_factory,
        record_service,
        community_get_or_create,
        workflow="record_owner_in_record_community",
        urls=urls,
        results=(200, 200, 200, 403),
    )


def test_record_owners_in_default_record_community_needs(
    community_owner,
    urls,
    users,
    logged_client,
    community_get_or_create,
    draft_with_community_factory,
    record_service,
    search_clear,
) -> None:
    _record_owners_in_record_community_test(
        community_owner,
        users,
        logged_client,
        draft_with_community_factory,
        record_service,
        community_get_or_create,
        workflow="record_owner_in_default_record_community",
        urls=urls,
        results=(200, 200, 403, 403),
    )
