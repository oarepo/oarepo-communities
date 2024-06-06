from invenio_access.permissions import system_identity


def published_record_in_community(client, community_id, record_service, user):
    # skip the request approval
    response = _create_record_in_community(client, community_id)
    record_item = record_service.publish(system_identity, response.json["id"])
    return record_item._obj


def _create_record_in_community(client, comm_id):
    return client.post(f"/communities/{comm_id}/thesis/records", json={})


def link_api2testclient(api_link):
    base_string = "https://127.0.0.1:5000/api/"
    return api_link[len(base_string) - 1 :]
