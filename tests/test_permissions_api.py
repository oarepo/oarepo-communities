from time import sleep

from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_pidstore.errors import PIDDoesNotExistError

from oarepo_runtime.cf.mappings import prepare_cf_indices
from tests.conftest import _community_get_or_create
from thesis.resources.record_communities.config import (
    ThesisRecordCommunitiesResourceConfig,
)

RECORD_COMMUNITIES_BASE_URL = ThesisRecordCommunitiesResourceConfig.url_prefix


def _create_and_publish(client, input_data, community, publish_authorized):
    """Create a draft and publish it."""
    # Create the draft
    response = client.post(
        RECORD_COMMUNITIES_BASE_URL, json=input_data
    )

    assert response.status_code == 201

    recid = response.json["id"]
    add = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/communities",
        json={
            "communities": [
                {"id": community.data["slug"]},  # test with slug
            ]
        },
    )

    # Publish it
    response = client.post(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/draft/actions/publish"
    )
    if publish_authorized:
        assert response.status_code == 202
    else:
        assert response.status_code == 403
    return recid



def _resp_to_input(resp):
    return {
        "slug": resp["slug"],
        "metadata": resp["metadata"],
        "access": resp["access"],
        "id": resp["id"],
    }


def _community_with_permissions_cf(community, identity, community_permissions_cf):
    data = _resp_to_input(community.data)
    data |= community_permissions_cf
    community = current_communities.service.update(identity, data["id"], data)
    Community.index.refresh()
    return community


def _recid_with_community(
    owner_client,
    input_data,
    community,
    community_owner,
    community_permissions_cf,
    publish_authorized=True
):
    comm = _community_with_permissions_cf(community, community_owner.identity, community_permissions_cf)
    recid = _create_and_publish(owner_client, input_data, comm, publish_authorized)
    return recid




def test_owner(client, community_owner, rando_user, community, community_permissions_cf, input_data, vocab_cf, search_clear):
    owner_client = community_owner.login(client)
    recid = _recid_with_community(owner_client, input_data, community, community_owner, community_permissions_cf)

    response_read = owner_client.get(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    assert response_read.status_code == 200
    response_delete = owner_client.delete(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    assert response_delete.status_code == 204
    response_read = owner_client.get(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    assert response_read.status_code == 410
    """
    jsn = response_read.json["metadata"]
    jsn["title"] = "updated title"
    response_update = owner_client.put(f"{RECORD_COMMUNITIES_BASE_URL}{recid}", json=jsn)
    response_read = owner_client.get(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    print()
    """

def test_cf(client, community_owner, community, community_permissions_cf, input_data, vocab_cf, search_clear):
    community_owner.login(client)
    recid = _recid_with_community(client, input_data, community, community_owner, community_permissions_cf)
    #sleep(5)
    response = client.get(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}/communities"
    )
    assert response.json['hits']['hits'][0]["custom_fields"] == community_permissions_cf["custom_fields"]

def test_reader(client, community_owner, community_reader, community, community_permissions_cf, input_data, vocab_cf, search_clear):
    reader_client = community_reader.login(client)
    recid = _recid_with_community(reader_client, input_data, community, community_owner, community_permissions_cf)

    response_read = reader_client.get(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    assert response_read.status_code == 200
    response_delete = reader_client.delete(
        f"{RECORD_COMMUNITIES_BASE_URL}{recid}"
    )
    assert response_delete.status_code == 403

def test_rando(client, community_owner, rando_user, community, community_permissions_cf, input_data, vocab_cf, search_clear):
    rando_client = rando_user.login(client)
    _recid_with_community(rando_client, input_data, community, community_owner, community_permissions_cf, publish_authorized=False)
