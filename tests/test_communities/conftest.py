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
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_permissions.generators import SystemProcess
from oarepo_requests.receiver import default_workflow_receiver_function
from oarepo_runtime.services.generators import RecordOwners
from oarepo_workflows import (
    AutoApprove,
    Workflow,
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)
from oarepo_workflows.permissions.generators import CreatorsFromWorkflow, IfInState
from thesis.proxies import current_record_communities_service
from thesis.records.api import ThesisDraft

from oarepo_communities.permissions.generators import CommunityMembers, CommunityRole
from oarepo_communities.permissions.presets import CommunityDefaultWorkflowPermissions
from oarepo_communities.records.models import CommunityWorkflowModel


@pytest.fixture()
def scenario_permissions():
    from invenio_requests.services.permissions import PermissionPolicy

    # RecipientsFromWorkflow
    requests = type(
        "RequestsPermissionPolicy",
        (PermissionPolicy,),
        dict(
            can_create=[
                SystemProcess(),
                CreatorsFromWorkflow(),
            ],
        ),
    )

    return requests


@pytest.fixture
def patch_requests_permissions(
    requests_service_config,
    scenario_permissions,
):
    setattr(requests_service_config, "permission_policy_cls", scenario_permissions)


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


class DefaultRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [RecordOwners()])],
        recipients=[
            CommunityRole("owner", access_key="record.parent.communities.default.id")
        ],
        transitions=WorkflowTransitions(
            submitted="publishing", approved="published", rejected="draft"
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[
            CommunityRole("owner", access_key="record.parent.communities.default.id")
        ],
        transitions=WorkflowTransitions(
            submitted="deleting", approved="deleted", rejected="published"
        ),
    )
    edit_published_record = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(),
    )
    secondary_community_submission = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )
    remove_secondary_community = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )
    community_migration = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )


class NoRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        requesters=[],
        recipients=[
            CommunityRole("owner", access_key="record.parent.communities.default.id")
        ],
        transitions=WorkflowTransitions(
            submitted="publishing", approved="published", rejected="draft"
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[],
        recipients=[
            CommunityRole("owner", access_key="record.parent.communities.default.id")
        ],
        transitions=WorkflowTransitions(
            submitted="deleting", approved="deleted", rejected="published"
        ),
    )
    edit_published_record = WorkflowRequest(
        requesters=[],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(),
    )
    secondary_community_submission = WorkflowRequest(
        requesters=[],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )
    remove_secondary_community = WorkflowRequest(
        requesters=[],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )
    community_migration = WorkflowRequest(
        requesters=[],
        recipients=[CommunityRole("owner", access_key="data.payload.community")],
        transitions=WorkflowTransitions(),
    )


WORKFLOWS = {
    "default": Workflow(
        label=_("Default workflow"),
        permissions_cls=CommunityDefaultWorkflowPermissions,
        requests_cls=DefaultRequests,
    ),
    "no": Workflow(
        label=_("Workflow with approval process"),
        permissions_cls=CommunityDefaultWorkflowPermissions,
        requests_cls=NoRequests,
    ),
}


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

    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }
    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["REQUESTS_REGISTERED_TYPES"] = [RequestType()]
    app_config["GLOBAL_SEARCH_MODELS"] = [
        {
            "model_service": "thesis.services.records.service.ThesisService",
            "service_config": "thesis.services.records.config.ThesisServiceConfig",
        }
    ]

    app_config["OAREPO_REQUESTS_DEFAULT_RECEIVER"] = default_workflow_receiver_function
    app_config["WORKFLOWS"] = WORKFLOWS

    app_config["REQUEST_TYPE_RECEIVER_ACCESS_KEYS"] = {  # possibility
        "publish_draft": {"community_role": "record.parent.communities.default.id"}
    }

    return app_config


@pytest.fixture()
def init_cf(app, db, cache):
    from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices

    prepare_cf_indices()

    result = app.test_cli_runner().invoke(create_communities_custom_field, [])
    assert result.exit_code == 0
    Community.index.refresh()


@pytest.fixture()
def community_owner(UserFixture, app, db):
    u = UserFixture(
        email="community_owner@inveniosoftware.org",
        password="community_owner",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_curator(UserFixture, app, db, community, inviter):
    u = UserFixture(
        email="community_curator@inveniosoftware.org",
        password="community_curator",
    )
    u.create(app, db)
    inviter(u.id, str(community.id), "curator")
    return u


@pytest.fixture()
def community_reader(UserFixture, app, db, community, inviter):
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
    return _community_get_or_create(community_owner.identity, minimal_community)


@pytest.fixture()
def community_with_default_workflow(community, init_cf, set_community_workflow):
    set_community_workflow(community.id)
    return community


@pytest.fixture()
def community_with_workflow_factory(minimal_community, init_cf, set_community_workflow):
    def create_community(slug, community_owner, workflow="default"):
        minimal_community_actual = copy.deepcopy(minimal_community)
        minimal_community_actual["slug"] = slug
        community = _community_get_or_create(
            community_owner.identity, minimal_community_actual
        )
        community_owner.identity.provides.add(
            CommunityRoleNeed(community.data["id"], "owner")
        )
        set_community_workflow(community.id, workflow=workflow)
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
            identity=identity,
            data={},
            request_type=RequestType,
            receiver=receiver,
            **kwargs,
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
            "label": "My Community : owner",
            "links": {
                "self": f"https://127.0.0.1:5000/api/communities/{community_id}",
                "self_html": "https://127.0.0.1:5000/communities/public",  # todo is this correct?
            },
            "reference": {"community_role": f"{community_id} : owner"},
            "type": "community role",
        }

    return _ui_serialized_community


from sqlalchemy.exc import NoResultFound


@pytest.fixture
def set_community_workflow(db):
    def _set_community_workflow(community_id, workflow="default"):
        try:
            record = CommunityWorkflowModel.query.filter(
                CommunityWorkflowModel.community_id == community_id
            ).one()
            record.query.update({"workflow": workflow})
            db.session.commit()
        except NoResultFound:
            obj = CommunityWorkflowModel(
                community_id=str(community_id),
                workflow=workflow,
            )
            db.session.add(obj)

    return _set_community_workflow


@pytest.fixture()
def requests_service_config():
    from invenio_requests.services.requests.config import RequestsServiceConfig

    return RequestsServiceConfig
