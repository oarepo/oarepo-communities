import os

import pytest
import yaml
from invenio_access.permissions import system_identity
from invenio_app.factory import create_api
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_communities.generators import CommunityRoleNeed
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.services.uow import RecordCommitOp, UnitOfWork
from thesis.proxies import current_service
from thesis.records.api import ThesisDraft, ThesisRecord


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"../thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture()
def input_data(sample_metadata_list):
    return sample_metadata_list[0]


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
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

    return app_config


@pytest.fixture(scope="function")
def sample_draft(app, db, input_data):
    with UnitOfWork(db.session) as uow:
        record = ThesisDraft.create(input_data)
        uow.register(RecordCommitOp(record, current_service.indexer, True))
        uow.commit()
        return record


@pytest.fixture()
def vocab_cf(app, db, cache):
    from oarepo_runtime.cf.mappings import prepare_cf_indices

    prepare_cf_indices()


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
def community_owner_helper(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_owner@inveniosoftware.org",
        password="community_owner",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_curator_helper(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_curator@inveniosoftware.org",
        password="community_curator",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_manager_helper(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_manager@inveniosoftware.org",
        password="community_manager",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_reader_helper(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_reader@inveniosoftware.org",
        password="community_reader",
    )
    u.create(app, db)
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


@pytest.fixture()
def community_permissions_cf():
    return {
        "custom_fields": {
            "permissions": {
                "owner": {
                    "can_publish": True,
                    "can_read": True,
                    "can_update": True,
                    "can_delete": True,
                },
                "manager": {
                    "can_publish": True,
                    "can_read": False,
                    "can_update": False,
                    "can_delete": False,
                },
                "curator": {
                    "can_publish": True,
                    "can_read": True,
                    "can_update": True,
                    "can_delete": False,
                },
                "reader": {
                    "can_publish": True,
                    "can_read": True,
                    "can_update": False,
                    "can_delete": False,
                },
            }
        }
    }


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


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


def _community_get_or_create(community_dict, identity):
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
    return c


@pytest.fixture()
def community(app, community_owner_helper, minimal_community):
    """Get the current RDM records service."""
    return _community_get_or_create(minimal_community, community_owner_helper.identity)


@pytest.fixture()
def community_owner(UserFixture, community_owner_helper, community, inviter, app, db):
    # inviter(community_owner_helper.id, community.id, "owner")
    community_owner_helper.identity.provides.add(
        CommunityRoleNeed(community.data["id"], "owner")
    )
    return community_owner_helper


"""
@pytest.fixture()
def community_manager(UserFixture, community_owner_helper, community, inviter, app, db):
    #inviter(community_owner_helper.id, community.id, "owner")
    community_owner_helper.identity.provides.add(CommunityRoleNeed(community.data["id"], "manager"))
    return community_owner_helper

@pytest.fixture()
def community_curator(UserFixture, community_owner_helper, community, inviter, app, db):
    #inviter(community_owner_helper.id, community.id, "owner")
    community_owner_helper.identity.provides.add(CommunityRoleNeed(community.data["id"], "curator"))
    return community_owner_helper
"""


@pytest.fixture()
def community_reader(UserFixture, community_reader_helper, community, inviter, app, db):
    inviter(community_reader_helper.id, community.data["id"], "reader")
    return community_reader_helper
