#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from pytest_oarepo.communities.functions import invite


def _serialized_community_role(id_) -> dict:
    return {
        "community": {
            "access": {
                "member_policy": "open",
                "members_visibility": "public",
                "record_policy": "open",
                "review_policy": "closed",
                "visibility": "public",
            },
            "children": {"allow": False},
            "custom_fields": {"workflow": "default"},
            "deletion_status": {"is_deleted": False, "status": "P"},
            "id": id_,
            "links": {},
            "metadata": {"title": "My Community"},
            "revision_id": 2,
            "slug": "public",
        },
        "id": f"{id_}:owner",
        "role": "owner",
        "links": {},
    }


def _check_result(response_community_role, id_) -> None:
    response_community_role["community"].pop("created")
    response_community_role["community"].pop("updated")
    assert response_community_role == _serialized_community_role(id_)


def _check_result_pick_resolved_field(response_community_role, id_) -> None:
    # this comes from the result of pick_resolver_fields of the CommunityRoleProxy method;
    # the read method of the service uses the ResultItem serialization; result might be different
    response_community_role["links"] = {}
    _check_result(response_community_role, id_)


def test_read(app, community):
    service = current_service_registry.get("community-role")
    community_id = str(community.id)
    id_ = f"{community_id}:owner"
    result = service.read(system_identity, id_)
    r = result.to_dict()
    _check_result(r, community_id)


def test_expand_community_role(
    logged_client,
    community_owner,
    users,
    community,
    draft_with_community_factory,
    submit_request_on_draft,
    ui_serialized_community_role,
    link2testclient,
    search_clear,
):
    reader = users[0]
    invite(reader, community.id, "reader")
    owner_client = logged_client(community_owner)

    record_id = draft_with_community_factory(reader.identity, community.id)["id"]
    submit = submit_request_on_draft(reader.identity, record_id, "publish_draft")

    owner_client.get(link2testclient(submit["links"]["self"]))
    read_expanded = owner_client.get(f"{link2testclient(submit['links']['self'])}?expand=true")
    assert read_expanded.status_code == 200
    ui_data = owner_client.get(
        f"{link2testclient(submit['links']['self'])}?expand=true",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    ).json  # expanded isn't here bc it isn't in the ui serialization schema
    assert "expanded" not in ui_data
    receiver = read_expanded.json["expanded"]["receiver"]
    _check_result_pick_resolved_field(receiver, str(community.id))
