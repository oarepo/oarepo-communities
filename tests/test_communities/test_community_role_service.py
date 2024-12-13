from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from .conftest import link_api2testclient
from .test_community_requests import _submit_request
from .utils import _create_record_in_community


def _serialized_community_role(id_):
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
            # "created": "2024-10-31T10:44:13.951403+00:00",
            "custom_fields": {"workflow": "default"},
            "deletion_status": {"is_deleted": False, "status": "P"},
            "id": id_,
            "links": {},
            "metadata": {"title": "My Community"},
            "revision_id": 2,
            "slug": "public",
            # "updated": "2024-10-31T10:44:14.012001+00:00",
        },
        "id": f"{id_}:owner",
        "role": "owner",
        "links": {},
    }


def _check_result(response_community_role, id_):
    response_community_role["community"].pop("created")
    response_community_role["community"].pop("updated")
    assert response_community_role == _serialized_community_role(id_)


def _check_result_pick_resolved_field(response_community_role, id_):
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
    community_reader,
    community,
    request_data_factory,
    record_service,
    ui_serialized_community_role,
    search_clear,
):
    reader_client = logged_client(community_reader)
    owner_client = logged_client(community_owner)

    record_id = _create_record_in_community(reader_client, community.id).json["id"]
    submit = _submit_request(
        reader_client,
        community.id,
        "thesis_draft",
        record_id,
        "publish_draft",
        request_data_factory,
    )

    read = owner_client.get(link_api2testclient(submit.json["links"]["self"]))
    read_expanded = owner_client.get(
        f"{link_api2testclient(submit.json['links']['self'])}?expand=true"
    )
    assert read_expanded.status_code == 200
    read_expanded_ui_serialization = owner_client.get(
        f"{link_api2testclient(submit.json['links']['self'])}?expand=true",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    ).json  # expanded isn't here bc it isn't in the ui serialization schema
    receiver = read_expanded.json["expanded"]["receiver"]
    _check_result_pick_resolved_field(receiver, str(community.id))
