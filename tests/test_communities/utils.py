from invenio_access.permissions import system_identity


def published_record_in_community(client, community_id, record_service, user):
    # skip the request approval
    response = _create_record_in_community(client, community_id)
    record_item = record_service.publish(system_identity, response.json["id"])
    return record_item._obj


def _create_record_in_community(client, comm_id, custom_workflow=None):
    if custom_workflow:
        return client.post(
            f"/communities/{comm_id}/thesis",
            json={"parent": {"workflow": custom_workflow}},
        )

    return client.post(f"/communities/{comm_id}/thesis", json={})


def link_api2testclient(api_link):
    base_string = "https://127.0.0.1:5000/api/"
    return api_link[len(base_string) - 1 :]

def pick_request_type(types_list, queried_type):
    for type in types_list:
        if type["type_id"] == queried_type:
            return type
    return None