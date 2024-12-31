import copy
import os

import pytest
import yaml
from flask_security import login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_communities.cli import create_communities_custom_field
from invenio_communities.communities.records.api import Community
from invenio_communities.generators import CommunityRoleNeed
from invenio_communities.proxies import current_communities
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from oarepo_requests.receiver import default_workflow_receiver_function
from oarepo_requests.services.permissions.generators import RequestActive
from oarepo_requests.services.permissions.workflow_policies import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)
from oarepo_runtime.services.permissions import RecordOwners
from oarepo_workflows import (
    AutoApprove,
    IfInState,
    Workflow,
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)
from thesis.records.api import ThesisDraft

from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.services.custom_fields.workflow import WorkflowCF
from oarepo_communities.services.permissions.generators import (
    CommunityMembers,
    CommunityRole,
    DefaultCommunityRole,
    RecordOwnerInDefaultRecordCommunity,
    RecordOwnerInRecordCommunity,
    TargetCommunityRole,
)
from oarepo_communities.services.permissions.policy import (
    CommunityDefaultWorkflowPermissions,
)
from tests.test_communities.utils import link_api2testclient


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"tests/thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture()
def record_service():
    return current_service


@pytest.fixture()
def community_inclusion_service():
    return current_oarepo_communities.community_inclusion_service


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


class TestCommunityWorkflowPermissions(CommunityDefaultWorkflowPermissions):
    can_read = [
        RecordOwners(),
        AuthenticatedUser(),  # need for request receivers - temporary
        CommunityRole("owner"),
        IfInState(
            "published",
            [AnyUser()],
        ),
    ]

    can_create = [
        DefaultCommunityRole("owner"),
        DefaultCommunityRole("reader"),
    ]

    can_update = [
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("published", [CommunityRole("owner")]),
    ]

    can_delete = [
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("deleting", [RequestActive()]),
    ]


class TestWithCuratorCommunityWorkflowPermissions(TestCommunityWorkflowPermissions):
    can_read = TestCommunityWorkflowPermissions.can_read + [
        DefaultCommunityRole("curator")
    ]

    can_create = TestCommunityWorkflowPermissions.can_create + [
        DefaultCommunityRole("curator")
    ]


class TestWithRecordOwnerInRecordCommunityWorkflowPermissions(
    TestWithCuratorCommunityWorkflowPermissions
):
    can_read = [
        RecordOwnerInRecordCommunity(),
        CommunityRole("owner"),
        IfInState(
            "published",
            [AnyUser()],
        ),
    ]

    can_create = TestCommunityWorkflowPermissions.can_create + [AuthenticatedUser()]


class TestWithRecordOwnerInDefaultRecordCommunityWorkflowPermissions(
    TestWithCuratorCommunityWorkflowPermissions
):
    can_read = [
        RecordOwnerInDefaultRecordCommunity(),
        CommunityRole("owner"),
        IfInState(
            "published",
            [AnyUser()],
        ),
    ]


class DefaultRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [RecordOwnerInDefaultRecordCommunity()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing", accepted="published", declined="draft"
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="deleting", accepted="deleted", declined="published"
        ),
    )
    edit_published_record = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(),
    )
    secondary_community_submission = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )
    remove_secondary_community = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )
    initiate_community_migration = WorkflowRequest(
        requesters=[CommunityMembers()],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )
    confirm_community_migration = WorkflowRequest(
        requesters=[SystemProcess()],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )


class PublishRequestsRecordOwnerInRecordCommunity(DefaultRequests):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [RecordOwnerInRecordCommunity()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing", accepted="published", declined="draft"
        ),
    )


class PublishRequestsRecordOwnerInDefaultRecordCommunity(DefaultRequests):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [RecordOwnerInDefaultRecordCommunity()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing", accepted="published", declined="draft"
        ),
    )


class NoRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        requesters=[],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing", accepted="published", declined="draft"
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="deleting", accepted="deleted", declined="published"
        ),
    )
    edit_published_record = WorkflowRequest(
        requesters=[],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(),
    )
    secondary_community_submission = WorkflowRequest(
        requesters=[],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )
    remove_secondary_community = WorkflowRequest(
        requesters=[],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )
    community_migration = WorkflowRequest(
        requesters=[],
        recipients=[TargetCommunityRole("owner")],
        transitions=WorkflowTransitions(),
    )


class CuratorPublishRequests(DefaultRequests):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [CommunityRole("owner")])],
        recipients=[DefaultCommunityRole("curator")],
        transitions=WorkflowTransitions(
            submitted="publishing", accepted="published", declined="draft"
        ),
    )


WORKFLOWS = {
    "default": Workflow(
        label=_("Default workflow"),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=DefaultRequests,
    ),
    "custom": Workflow(
        label=_("For checking if workflow changed."),
        permission_policy_cls=TestWithCuratorCommunityWorkflowPermissions,
        request_policy_cls=DefaultRequests,
    ),
    "record_owner_in_record_community": Workflow(
        label=_("For testing RecordOwnerInRecordCommunity generator."),
        permission_policy_cls=TestWithRecordOwnerInRecordCommunityWorkflowPermissions,
        request_policy_cls=PublishRequestsRecordOwnerInRecordCommunity,
    ),
    "record_owner_in_default_record_community": Workflow(
        label=_("For testing RecordOwnerInDefaultRecordCommunity generator."),
        permission_policy_cls=TestWithRecordOwnerInDefaultRecordCommunityWorkflowPermissions,
        request_policy_cls=PublishRequestsRecordOwnerInDefaultRecordCommunity,
    ),
    "no": Workflow(
        label=_("Can't do any requests."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=NoRequests,
    ),
    "curator_publish": Workflow(
        label=_("For testing assigned param filter."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=CuratorPublishRequests,
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


@pytest.fixture()
def remover():
    """Add/invite a user to a community with a specific role."""

    def remove(user_id, community_id):
        """Add/invite a user to a community with a specific role."""
        delete_data = {
            "members": [{"type": "user", "id": user_id}],
        }
        member_delete = current_communities.service.members.delete(
            system_identity, community_id, delete_data
        )

    return remove


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
            "api_resource_config": "thesis.resources.records.config.ThesisResourceConfig",
        }
    ]

    app_config["OAREPO_REQUESTS_DEFAULT_RECEIVER"] = default_workflow_receiver_function
    app_config["WORKFLOWS"] = WORKFLOWS

    app_config["COMMUNITIES_CUSTOM_FIELDS"] = [WorkflowCF(name="workflow")]
    app_config["COMMUNITIES_CUSTOM_FIELDS_UI"] = []
    app_config["I18N_LANGUAGES"] = [
        ("cs", _("Czech")),
    ]

    app_config["REQUESTS_PERMISSION_POLICY"] = (
        CreatorsFromWorkflowRequestsPermissionPolicy
    )
    return app_config


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
def community_curator(UserFixture, app, db):
    u = UserFixture(
        email="community_curator@inveniosoftware.org",
        password="community_curator",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def rando_user(UserFixture, app, db):
    # communityless user
    u = UserFixture(
        email="just_a_traveller@random.gov",
        password="not_a_federal_agent",
    )
    u.create(app, db)
    return u


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


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


def _community_get_or_create(identity, community_dict, workflow=None):
    """Util to get or create community, to avoid duplicate error."""
    slug = community_dict["slug"]
    try:
        c = current_communities.service.record_cls.pid.resolve(slug)
    except PIDDoesNotExistError:
        c = current_communities.service.create(
            identity,
            {**community_dict, "custom_fields": {"workflow": workflow or "default"}},
        )
        Community.index.refresh()
        identity.provides.add(CommunityRoleNeed(str(c.id), "owner"))
    return c


@pytest.fixture()
def community(app, minimal_community, community_owner):
    return _community_get_or_create(
        community_owner.identity, minimal_community, workflow="default"
    )


@pytest.fixture()
def communities(app, minimal_community, community_owner):
    return {
        "aaa": _community_get_or_create(
            community_owner.identity,
            {
                **minimal_community,
                "slug": "aaa",
            },
            workflow="default",
        ),
        "bbb": _community_get_or_create(
            community_owner.identity,
            {
                **minimal_community,
                "slug": "bbb",
            },
            workflow="default",
        ),
    }


@pytest.fixture(autouse=True)
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
def community_with_workflow_factory(minimal_community, set_community_workflow):
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
def ui_serialized_community_role():
    def _ui_serialized_community(community_id):
        return {
            "label": "Owner of My Community",
            "reference": {"community_role": f"{community_id}:owner"},
            "type": "community role",
        }

    return _ui_serialized_community


@pytest.fixture
def ui_serialized_community():
    def _ui_serialized_community(community_id):
        return {
            "label": "My Community",
            "links": {
                "self": f"https://127.0.0.1:5000/api/communities/{community_id}",
                "self_html": "https://127.0.0.1:5000/communities/public",  # todo is this correct?
            },
            "reference": {"community": community_id},
            "type": "community",
        }

    return _ui_serialized_community


@pytest.fixture
def set_community_workflow():
    def _set_community_workflow(community_id, workflow="default"):
        community_item = current_communities.service.read(system_identity, community_id)
        current_communities.service.update(
            system_identity,
            community_id,
            data={**community_item.data, "custom_fields": {"workflow": workflow}},
        )

    return _set_community_workflow


@pytest.fixture()
def requests_service_config():
    from invenio_requests.services.requests.config import RequestsServiceConfig

    return RequestsServiceConfig


@pytest.fixture()
def default_workflow_json():
    return {"parent": {"workflow": "default"}}


@pytest.fixture()
def create_draft_via_resource(default_workflow_json):
    def _create_draft(
        client,
        community,
        expand=True,
        custom_workflow=None,
        additional_data=None,
        **kwargs,
    ):
        json = copy.deepcopy(default_workflow_json)
        if custom_workflow:
            json["parent"]["workflow"] = custom_workflow
        if additional_data:
            json |= additional_data
        # url = "/thesis/" + "?expand=true" if expand else "/thesis/"
        url = f"/communities/{community.id}/thesis"
        return client.post(url, json=json, **kwargs)

    return _create_draft


@pytest.fixture()
def get_request_type():
    """
    gets request create link from serialized request types
    """

    def _get_request_type(request_types_json, request_type):
        selected_entry = [
            entry for entry in request_types_json if entry["type_id"] == request_type
        ][0]
        return selected_entry

    return _get_request_type


@pytest.fixture()
def get_request_link(get_request_type):
    """
    gets request create link from serialized request types
    """

    def _create_request_from_link(request_types_json, request_type):
        selected_entry = get_request_type(request_types_json, request_type)
        return selected_entry["links"]["actions"]["create"]

    return _create_request_from_link


@pytest.fixture
def create_request_by_link(get_request_link):
    def _create_request(client, record, request_type):
        applicable_requests = client.get(
            link_api2testclient(record.json["links"]["applicable-requests"])
        ).json["hits"]["hits"]
        create_link = link_api2testclient(
            get_request_link(applicable_requests, request_type)
        )
        create_response = client.post(create_link)
        return create_response

    return _create_request


@pytest.fixture
def submit_request_by_link(create_request_by_link):
    def _submit_request(client, record, request_type):
        create_response = create_request_by_link(client, record, request_type)
        submit_response = client.post(
            link_api2testclient(create_response.json["links"]["actions"]["submit"])
        )
        return submit_response

    return _submit_request


@pytest.fixture()
def clear_babel_context():

    # force babel reinitialization when language is switched
    def _clear_babel_context():
        try:
            from flask import g
            from flask_babel import SimpleNamespace

            g._flask_babel = SimpleNamespace()
        except ImportError:
            return

    return _clear_babel_context
