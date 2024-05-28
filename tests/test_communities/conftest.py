import copy
import os

import pytest
import yaml
from flask_security import login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_communities import current_communities
from invenio_communities.cli import create_communities_custom_field
from invenio_communities.communities.records.api import Community
from invenio_communities.generators import CommunityRoleNeed
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.services.uow import RecordCommitOp, UnitOfWork
from thesis.proxies import current_record_communities_service
from thesis.records.api import ThesisDraft, ThesisRecord


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"tests/thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture()
def record_service():
    return current_service


@pytest.fixture()
def record_communities_service():
    return current_record_communities_service


@pytest.fixture()
def input_data(sample_metadata_list):
    return sample_metadata_list[0]


class LoggedClient:
    def __init__(self, client, user_fixture):
        self.client = client
        self.user_fixture = user_fixture

    def _login(self):
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args, **kwargs):
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._login()
        return self.client.delete(*args, **kwargs)


@pytest.fixture()
def logged_client(client):
    def _logged_client(user):
        return LoggedClient(client, user)

    return _logged_client


@pytest.fixture()
def inviter():
    """Add/invite a user to a community with a specific role."""

    def invite(user_id, community_id, role):
        """Add/invite a user to a community with a specific role."""
        invitation_data = {
            "members": [
                {
                    "type": "user",
                    "id": user_id,
                }
            ],
            "role": role,
            "visible": True,
        }
        current_communities.service.members.add(
            system_identity, community_id, invitation_data
        )

    return invite


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )
    app_config["RATELIMIT_AUTHENTICATED_USER"] = "200 per second"
    app_config["SEARCH_HOSTS"] = [
        {
            "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
            "port": os.environ.get("OPENSEARCH_PORT", "9200"),
        }
    ]
    # disable redis cache
    app_config["CACHE_TYPE"] = "SimpleCache"  # Flask-Caching related configs
    app_config["CACHE_DEFAULT_TIMEOUT"] = 300

    from oarepo_communities.cf.permissions import PermissionsCF

    app_config["COMMUNITIES_CUSTOM_FIELDS"] = [PermissionsCF("permissions")]

    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }
    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["REQUESTS_REGISTERED_TYPES"] = [RequestType()]

    def default_receiver(*args, **kwargs):
        return args[0]

    # generalize this for all receiver types once?
    def receiver_publish(*args, **kwargs):
        topic = args[2]
        return {"community": str(topic.parent.communities.default.id)}

    def receiver_delete(*args, **kwargs):
        topic = args[2]
        return {"community": str(topic.parent.communities.default.id)}

    def receiver_adressed(*args, **kwargs):
        data = args[4]
        target_community = data["payload"]["community"]
        return {"community": target_community}

    app_config["OAREPO_REQUESTS_DEFAULT_RECEIVER"] = {
        "thesis_community_migration": receiver_adressed,
        "thesis_delete_record": receiver_delete,
        "thesis_publish_draft": receiver_publish,
        "thesis_remove_secondary_community": receiver_adressed,
        "thesis_secondary_community_submission": receiver_adressed,
    }

    return app_config


@pytest.fixture()
def init_cf(app, db, cache):
    from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices

    prepare_cf_indices()

    result = app.test_cli_runner().invoke(create_communities_custom_field, [])
    assert result.exit_code == 0
    Community.index.refresh()


@pytest.fixture
def example_record(app, db, input_data):
    # record = current_service.create(system_identity, sample_data[0])
    # return record
    with UnitOfWork(db.session) as uow:
        record = ThesisRecord.create(input_data)
        uow.register(RecordCommitOp(record, current_service.indexer, True))
        uow.commit()
        return record


@pytest.fixture()
def community_owner(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_owner@inveniosoftware.org",
        password="community_owner",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_curator(UserFixture, app, db, community, inviter):
    """Community owner."""
    u = UserFixture(
        email="community_curator@inveniosoftware.org",
        password="community_curator",
    )
    u.create(app, db)
    inviter(u.id, str(community.id), "curator")
    return u


@pytest.fixture()
def community_manager(UserFixture, app, db, community, inviter):
    """Community owner."""
    u = UserFixture(
        email="community_manager@inveniosoftware.org",
        password="community_manager",
    )
    u.create(app, db)
    inviter(u.id, str(community.id), "manager")
    return u


@pytest.fixture()
def community_reader(UserFixture, app, db, community, inviter):
    """Community owner."""
    u = UserFixture(
        email="community_reader@inveniosoftware.org",
        password="community_reader",
    )
    u.create(app, db)
    inviter(u.id, str(community.id), "reader")
    return u


@pytest.fixture()
def rando_user(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="rando@inveniosoftware.org",
        password="rando",
    )
    u.create(app, db)
    return u


@pytest.fixture(scope="module")
def minimal_community():
    """Minimal community metadata."""
    return {
        "access": {
            "visibility": "public",
            "record_policy": "open",
        },
        "slug": "public",
        "metadata": {
            "title": "My Community",
        },
    }


@pytest.fixture
def community_permissions_cf():
    return {
        "custom_fields": {
            "permissions": {
                "owner": {
                    "can_create_in_community": True,
                    "can_submit_to_community": True,
                    "can_submit_secondary_community": True,
                    "can_remove_secondary_community": True,
                    "can_search_drafts": True,
                    "can_publish_request": True,
                    "can_delete_request": True,
                    "can_read": True,
                    "can_read_draft": True,
                    "can_update": True,
                    "can_search": True,
                    "can_create": True,
                },
                "reader": {
                    "can_create_in_community": True,
                    "can_submit_to_community": False,
                    "can_submit_secondary_community": False,
                    "can_remove_secondary_community": False,
                    "can_publish_request": False,
                    "can_delete_request": False,
                    "can_read": True,
                    "can_read_draft": True,
                    "can_update": False,
                    "can_delete": False,
                    "can_search": True,
                },
            }
        }
    }


@pytest.fixture
def community_permissions_cf_authenticated_user_read(community_permissions_cf):
    ret = copy.deepcopy(community_permissions_cf)
    ret["custom_fields"]["permissions"]["authenticated_user"] = {
        "can_read": True,
        "can_read_draft": True,
    }
    return ret


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


def _community_get_or_create(identity, community_dict):
    """Util to get or create community, to avoid duplicate error."""
    slug = community_dict["slug"]
    try:
        c = current_communities.service.record_cls.pid.resolve(slug)
    except PIDDoesNotExistError:
        c = current_communities.service.create(
            identity,
            community_dict,
        )
        Community.index.refresh()
        identity.provides.add(CommunityRoleNeed(str(c.id), "owner"))
    return c


@pytest.fixture()
def community(app, minimal_community, community_owner):
    """Get the current RDM records service."""
    return _community_get_or_create(community_owner.identity, minimal_community)


@pytest.fixture()
def community_with_permissions_cf(community, community_permissions_cf, init_cf):
    data = current_communities.service.read(system_identity, community.id).data
    data |= community_permissions_cf
    community = current_communities.service.update(system_identity, data["id"], data)
    Community.index.refresh()
    return community


@pytest.fixture()
def community_with_permission_cf_factory(
    minimal_community, init_cf, community_permissions_cf
):
    def create_community(slug, community_owner, community_permissions_cf_custom=None):
        community_permissions_cf_actual = (
            community_permissions_cf_custom or community_permissions_cf
        )
        minimal_community_actual = copy.deepcopy(minimal_community)
        minimal_community_actual["slug"] = slug
        community = _community_get_or_create(
            community_owner.identity, minimal_community_actual
        )
        community_owner.identity.provides.add(
            CommunityRoleNeed(community.data["id"], "owner")
        )
        data = community.data | community_permissions_cf_actual
        community = current_communities.service.update(
            system_identity, data["id"], data
        )
        Community.index.refresh()
        return community

    return create_community


# -----
from invenio_requests.customizations import RequestType
from invenio_requests.proxies import current_requests


@pytest.fixture(scope="module")
def requests_service(app):
    """Request Factory fixture."""

    return current_requests.requests_service


@pytest.fixture()
def create_publish_request(requests_service):
    """Request Factory fixture."""

    def _create_request(identity, receiver, **kwargs):
        """Create a request."""
        RequestType.allowed_receiver_ref_types = ["community"]
        RequestType.needs_context = {
            "community_permission_name": "can_publish",
        }
        # Need to use the service to get the id
        item = requests_service.create(
            identity, {}, RequestType, receiver=receiver, **kwargs
        )
        return item._request

    return _create_request


# -----
from thesis.proxies import current_service


@pytest.fixture(scope="function")
def sample_draft(app, db, input_data, community):
    input_data["community_id"] = community.id
    draft_item = current_service.create(system_identity, input_data)
    ThesisDraft.index.refresh()
    return ThesisDraft.pid.resolve(draft_item.id, registered_only=False)


@pytest.fixture
def request_data_factory():
    def _request_data(
        community_id, topic_type, topic_id, request_type, creator=None, payload=None
    ):
        input_data = {
            "request_type": request_type,
            "topic": {topic_type: topic_id},
        }
        if payload:
            input_data["payload"] = payload
        return input_data

    return _request_data


@pytest.fixture
def ui_serialized_community():
    def _ui_serialized_community(community_id):
        return {
            "label": "My Community",
            "link": f"https://127.0.0.1:5000/api/communities/{community_id}",
            "reference": {"community": community_id},
            "type": "community",
        }

    return _ui_serialized_community
