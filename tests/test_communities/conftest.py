import os

import pytest
from invenio_app.factory import create_api
from invenio_i18n import lazy_gettext as _
from invenio_notifications.backends import EmailNotificationBackend
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from invenio_records_resources.references.entity_resolvers import ServiceResultResolver
from oarepo_requests.notifications.builders.publish import (
    PublishDraftRequestAcceptNotificationBuilder,
    PublishDraftRequestSubmitNotificationBuilder,
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
from pytest_oarepo.vocabularies.config import VOCABULARIES_TEST_CONFIG
from thesis.proxies import current_service
from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices
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

from oarepo_runtime.i18n import lazy_gettext as _
from deepmerge import always_merger

pytest_plugins = [
    "pytest_oarepo.communities.fixtures",
    "pytest_oarepo.communities.records",
    "pytest_oarepo.requests.fixtures",
    "pytest_oarepo.records",
    "pytest_oarepo.fixtures",
    "pytest_oarepo.users",
    "pytest_oarepo.files",
    "pytest_oarepo.vocabularies"
]

@pytest.fixture(autouse=True)
def init_communities_cf(init_communities_cf):
    return init_communities_cf


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


@pytest.fixture()
def urls():
    return {"BASE_URL": "/thesis/", "BASE_URL_REQUESTS": "/requests/"}


@pytest.fixture()
def record_service():
    return current_service


@pytest.fixture()
def base_model_schema():
    return "local://thesis-1.0.0.json"


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

    can_read_deleted = can_read
    can_read_all_records = [
        RecordOwners(),
        CommunityRole("owner"),
        CommunityRole("curator"),
    ]

    can_create = [
        DefaultCommunityRole("owner"),
        DefaultCommunityRole("reader"),
    ]
    can_manage_files = can_create

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
        IfInState(
            "published",
            [AnyUser()],
        ),
    ]


class TestWithRecordOwnerInDefaultRecordCommunityWorkflowPermissions(
    TestWithCuratorCommunityWorkflowPermissions
):
    can_read = [
        RecordOwnerInDefaultRecordCommunity(),
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
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="deleting",
            accepted="deleted",
            declined="published",
            cancelled="published",
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
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )


class PublishRequestsRecordOwnerInDefaultRecordCommunity(DefaultRequests):
    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [RecordOwnerInDefaultRecordCommunity()])],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )


class NoRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        requesters=[],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )
    delete_published_record = WorkflowRequest(
        requesters=[],
        recipients=[DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="deleting",
            accepted="deleted",
            declined="published",
            cancelled="published",
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
        requesters=[
            IfInState("draft", [CommunityRole("owner"), CommunityRole("reader")])
        ],
        recipients=[DefaultCommunityRole("curator")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )

class MultipleRecipientsRequests(DefaultRequests):
    publish_draft = WorkflowRequest(
        requesters=[
            IfInState("draft", [CommunityRole("owner"), CommunityRole("reader")])
        ],
        recipients=[DefaultCommunityRole("curator"), DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
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
    "multiple_recipients": Workflow(
        label=_("For testing multiple recipient requests.."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=MultipleRecipientsRequests,
    ),
}


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

    app_config["NOTIFICATIONS_BACKENDS"] = {
        EmailNotificationBackend.id: EmailNotificationBackend(),
    }
    app_config["NOTIFICATIONS_BUILDERS"] = {
        PublishDraftRequestAcceptNotificationBuilder.type: PublishDraftRequestAcceptNotificationBuilder,
        PublishDraftRequestSubmitNotificationBuilder.type: PublishDraftRequestSubmitNotificationBuilder,
    }

    app_config["MAIL_DEFAULT_SENDER"] = "test@invenio-rdm-records.org"

    app_config["INVENIO_RDM_ENABLED"] = True
    app_config["RDM_MODELS"] = {
            "service_id": "thesis",
            # deprecated
            "model_service": "thesis.services.records.service.ThesisService",
            # deprecated
            "service_config": "thesis.services.records.config.ThesisServiceConfig",
            "api_service": "thesis.services.records.service.ThesisService",
            "api_service_config": "thesis.services.records.config.ThesisServiceConfig",
            "api_resource": "thesis.resources.records.resource.ThesisResource",
            "api_resource_config": (
                "thesis.resources.records.config.ThesisResourceConfig"
            ),
            "ui_resource_config": "tests.ui.thesis.ThesisUIResourceConfig",
            "record_cls": "thesis.records.api.ThesisRecord",
            "pid_type": "thesis",
            "draft_cls": "thesis.records.api.ThesisDraft",
            },
    always_merger.merge(app_config, VOCABULARIES_TEST_CONFIG)
    return app_config


from invenio_requests.customizations import RequestType


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
