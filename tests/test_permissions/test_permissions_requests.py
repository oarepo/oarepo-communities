import pytest
from invenio_records_resources.services.errors import PermissionDeniedError


def test_receiver_permissions_community_role(
    requests_service,
    community_with_permissions_cf,
    create_publish_request,
    community_owner,
    community_reader,
):
    publish_request = create_publish_request(
        identity=community_owner.identity,
        receiver={"oarepo_community": community_with_permissions_cf.id},
    )
    requests_service.execute_action(
        identity=community_owner.identity, id_=publish_request.id, action="submit"
    )

    with pytest.raises(PermissionDeniedError):
        reader_accept = requests_service.execute_action(
            identity=community_reader.identity, id_=publish_request.id, action="accept"
        )
    owner_accept = requests_service.execute_action(
        identity=community_owner.identity, id_=publish_request.id, action="accept"
    )


def test_receiver_permissions_community_role_perm_undefined(
    requests_service,
    community_with_permissions_cf,
    create_publish_request,
    community_owner,
    community_curator,
):
    publish_request = create_publish_request(
        identity=community_owner.identity,
        receiver={"oarepo_community": community_with_permissions_cf.id},
    )
    requests_service.execute_action(
        identity=community_owner.identity, id_=publish_request.id, action="submit"
    )

    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(
            identity=community_curator.identity, id_=publish_request.id, action="accept"
        )
