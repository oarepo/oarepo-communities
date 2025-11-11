#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import os

import pytest
from flask import Blueprint
from invenio_app.factory import create_api
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from oarepo_rdm import rdm_minimal_preset
from oarepo_requests.model.presets.requests import requests_preset
from oarepo_requests.receiver import default_workflow_receiver_function
from oarepo_requests.services.permissions.generators import RequestActive
from oarepo_requests.services.permissions.workflow_policies import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)
from oarepo_workflows import (
    AutoApprove,
    IfInState,
    Workflow,
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)
from oarepo_workflows.model.presets import workflows_preset

from oarepo_communities.model.presets import communities_preset
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

pytest_plugins = [
    "pytest_oarepo.communities.fixtures",
    "pytest_oarepo.communities.records",
    "pytest_oarepo.requests.fixtures",
    "pytest_oarepo.records",
    "pytest_oarepo.fixtures",
    "pytest_oarepo.users",
    "pytest_oarepo.files",
]


@pytest.fixture(scope="module")
def app(app):
    """Bp = Blueprint("communities_test_ui", __name__).

    @bp.route("/communities_test/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/communities_test/", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/communities_test/uploads/<pid_value>", methods=["GET"])  # draft self_html
    def deposit_edit(pid_value: str) -> str:
        return "deposit edit ok"

    @bp.route("/communities_test/uploads/new", methods=["GET"])
    def deposit_create() -> str:
        return "deposit create ok"

    @bp.route("/communities_test/records/<pid_value>")
    def record_detail(pid_value) -> str:
        return "detail ok"

    @bp.route("/communities_test/records/<pid_value>/latest", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/communities_test/records/<pid_value>/export/<export_format>", methods=["GET"])
    def export(pid_value, export_format: str) -> str:
        return "export ok"
    """
    bp = Blueprint("invenio_app_rdm_communities", __name__)

    @bp.route("/invenio_app_rdm_communities/communities_home", methods=["GET"])
    def communities_home(pid_value: str) -> str:
        return "communities_home ok"

    app.register_blueprint(bp)

    bp = Blueprint("community-records", __name__)

    @bp.route("/community-records/search", methods=["GET"])
    def search(pid_value: str) -> str:
        return "search ok"

    app.register_blueprint(bp)

    return app


@pytest.fixture(autouse=True)
def init_communities_custom_fields(init_communities_cf):
    return init_communities_cf


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


@pytest.fixture
def urls():
    return {"BASE_URL": "/communities-test", "BASE_URL_REQUESTS": "/requests"}


@pytest.fixture(scope="session")
def model_types():
    """Model types fixture."""
    # Define the model types used in the tests
    return {
        "Metadata": {
            "properties": {
                "title": {"type": "fulltext+keyword", "required": True},
                "creators": {
                    "type": "array",
                    "items": {"type": "keyword"},
                },
                "contributors": {
                    "type": "array",
                    "items": {"type": "keyword"},
                },
            }
        }
    }


@pytest.fixture(scope="session")
def communities_model(model_types):
    from oarepo_model.api import model

    model = model(
        name="communities_test",
        version="1.0.0",
        presets=[
            rdm_minimal_preset,
            workflows_preset,
            requests_preset,
            communities_preset,
        ],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
        configuration={},
    )
    model.register()
    return model


@pytest.fixture
def record_service(communities_model):
    return communities_model.proxies.current_service


@pytest.fixture
def requests_service():
    from oarepo_requests.proxies import current_requests_service

    return current_requests_service


@pytest.fixture
def base_model_schema():
    return "local://thesis-1.0.0.json"


class TestCommunityWorkflowPermissions(CommunityDefaultWorkflowPermissions):
    """Test workflow permissions with community roles."""

    can_read = (
        RecordOwners(),
        AuthenticatedUser(),  # need for request receivers - temporary
        CommunityRole("owner"),
        IfInState(
            "published",
            [AnyUser()],
        ),
    )

    can_read_all_records = (
        RecordOwners(),
        CommunityRole("owner"),
        CommunityRole("curator"),
    )

    can_create = (
        DefaultCommunityRole("owner"),
        DefaultCommunityRole("reader"),
    )
    can_manage_files = can_create

    can_update = (
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("published", [CommunityRole("owner")]),
    )

    can_delete = (
        IfInState("draft", [RecordOwners()]),
        IfInState("publishing", [RecordOwners()]),
        IfInState("deleting", [RequestActive()]),
    )


class TestWithCuratorCommunityWorkflowPermissions(TestCommunityWorkflowPermissions):
    """Like TestCommunityWorkflowPermissions but curator can read all records."""

    can_read = (
        *TestCommunityWorkflowPermissions.can_read,
        DefaultCommunityRole("curator"),
    )

    can_create = (
        *TestCommunityWorkflowPermissions.can_create,
        DefaultCommunityRole("curator"),
    )


class TestWithRecordOwnerInRecordCommunityWorkflowPermissions(TestWithCuratorCommunityWorkflowPermissions):
    """Like TestWithCuratorCommunityWorkflowPermissions but record owner in record community can read."""

    can_read = (
        RecordOwnerInRecordCommunity(),
        IfInState(
            "published",
            [AnyUser()],
        ),
    )


class TestWithRecordOwnerInDefaultRecordCommunityWorkflowPermissions(TestWithCuratorCommunityWorkflowPermissions):
    """Like TestWithCuratorCommunityWorkflowPermissions but record owner in default community can read."""

    can_read = (
        RecordOwnerInDefaultRecordCommunity(),
        IfInState(
            "published",
            [AnyUser()],
        ),
    )


class DefaultRequests(WorkflowRequestPolicy):
    """Default requests with record owner as the only requester."""

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
    """Like DefaultRequests but record owner in record community can submit publish request."""

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
    """Like DefaultRequests but record owner in default community can submit publish request."""

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
    """No requests are possible."""

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


class CuratorPublishRequests(DefaultRequests):
    """Workflow requests with curator as the only recipient."""

    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [CommunityRole("owner"), CommunityRole("reader")])],
        recipients=[DefaultCommunityRole("curator")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )


class MultipleRecipientsRequests(DefaultRequests):
    """Workflow requests with multiple recipients."""

    publish_draft = WorkflowRequest(
        requesters=[IfInState("draft", [CommunityRole("owner"), CommunityRole("reader")])],
        recipients=[DefaultCommunityRole("curator"), DefaultCommunityRole("owner")],
        transitions=WorkflowTransitions(
            submitted="publishing",
            accepted="published",
            declined="draft",
            cancelled="draft",
        ),
    )


WORKFLOWS = [
    Workflow(
        code="default",
        label=_("Default workflow"),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=DefaultRequests,
    ),
    Workflow(
        code="custom",
        label=_("For checking if workflow changed."),
        permission_policy_cls=TestWithCuratorCommunityWorkflowPermissions,
        request_policy_cls=DefaultRequests,
    ),
    Workflow(
        code="record_owner_in_record_community",
        label=_("For testing RecordOwnerInRecordCommunity generator."),
        permission_policy_cls=TestWithRecordOwnerInRecordCommunityWorkflowPermissions,
        request_policy_cls=PublishRequestsRecordOwnerInRecordCommunity,
    ),
    Workflow(
        code="record_owner_in_default_record_community",
        label=_("For testing RecordOwnerInDefaultRecordCommunity generator."),
        permission_policy_cls=TestWithRecordOwnerInDefaultRecordCommunityWorkflowPermissions,
        request_policy_cls=PublishRequestsRecordOwnerInDefaultRecordCommunity,
    ),
    Workflow(
        code="no",
        label=_("Can't do any requests."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=NoRequests,
    ),
    Workflow(
        code="curator_publish",
        label=_("For testing assigned param filter."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=CuratorPublishRequests,
    ),
    Workflow(
        code="multiple_recipients",
        label=_("For testing multiple recipient requests.."),
        permission_policy_cls=TestCommunityWorkflowPermissions,
        request_policy_cls=MultipleRecipientsRequests,
    ),
]


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"
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

    app_config["REQUESTS_PERMISSION_POLICY"] = CreatorsFromWorkflowRequestsPermissionPolicy

    """
    app_config["NOTIFICATIONS_BACKENDS"] = {
        EmailNotificationBackend.id: EmailNotificationBackend(),
    }

    app_config["NOTIFICATIONS_BUILDERS"] = {
        PublishDraftRequestAcceptNotificationBuilder.type: PublishDraftRequestAcceptNotificationBuilder,
        PublishDraftRequestSubmitNotificationBuilder.type: PublishDraftRequestSubmitNotificationBuilder,
    }
    always_merger.merge(app_config, VOCABULARIES_TEST_CONFIG)
    """

    app_config["MAIL_DEFAULT_SENDER"] = "test@invenio-rdm-records.org"

    app_config["INVENIO_RDM_ENABLED"] = True
    app_config["RDM_MODELS"] = (
        {
            "service_id": "thesis",
            # deprecated
            "model_service": "thesis.services.records.service.ThesisService",
            # deprecated
            "service_config": "thesis.services.records.config.ThesisServiceConfig",
            "api_service": "thesis.services.records.service.ThesisService",
            "api_service_config": "thesis.services.records.config.ThesisServiceConfig",
            "api_resource": "thesis.resources.records.resource.ThesisResource",
            "api_resource_config": ("thesis.resources.records.config.ThesisResourceConfig"),
            "ui_resource_config": "tests.ui.thesis.ThesisUIResourceConfig",
            "record_cls": "thesis.records.api.ThesisRecord",
            "pid_type": "thesis",
            "draft_cls": "thesis.records.api.ThesisDraft",
        },
    )

    return app_config


@pytest.fixture
def ui_serialized_community_role():
    def _ui_serialized_community(community_id: str) -> dict:
        return {
            "label": "Owner of My Community",
            "reference": {"community_role": f"{community_id}:owner"},
            "type": "community role",
        }

    return _ui_serialized_community


@pytest.fixture
def ui_serialized_community():
    def _ui_serialized_community(community_id: str) -> dict:
        return {
            "label": "My Community",
            "links": {
                "self": f"https://127.0.0.1:5000/api/communities/{community_id}",
                "self_html": "https://127.0.0.1:5000/communities/public",  # TODO: is this correct?
            },
            "reference": {"community": community_id},
            "type": "community",
        }

    return _ui_serialized_community


@pytest.fixture
def clear_babel_context():
    # force babel reinitialization when language is switched
    def _clear_babel_context() -> None:
        try:
            from flask import g
            from flask_babel import SimpleNamespace

            g._flask_babel = SimpleNamespace()  # noqa: SLF001
        except ImportError:
            return

    return _clear_babel_context
