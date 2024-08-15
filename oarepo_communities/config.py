from oarepo_runtime.i18n import lazy_gettext as _

from .cf.workflows import WorkflowCF, lazy_workflow_options
from .requests.migration import (
    ConfirmCommunityMigrationRequestType,
    InitiateCommunityMigrationRequestType,
)
from .requests.remove_secondary import RemoveSecondaryCommunityRequestType
from .requests.submission_secondary import SecondaryCommunitySubmissionRequestType
from .resolvers.ui import CommunityRoleUIResolver

REQUESTS_REGISTERED_TYPES = [
    InitiateCommunityMigrationRequestType(),
    ConfirmCommunityMigrationRequestType(),
    RemoveSecondaryCommunityRequestType(),
    SecondaryCommunitySubmissionRequestType(),
]
OAREPO_REQUESTS_DEFAULT_RECEIVER = (
    "oarepo_requests.receiver.default_workflow_receiver_function"
)
REQUESTS_ALLOWED_RECEIVERS = ["community_role"]

ENTITY_REFERENCE_UI_RESOLVERS = {
    "community_role": CommunityRoleUIResolver("community_role"),
}


DEFAULT_COMMUNITIES_CUSTOM_FIELDS = [
    WorkflowCF(name="workflow"),
    WorkflowCF(name="allowed_workflows", multiple=True),
]

DEFAULT_COMMUNITIES_CUSTOM_FIELDS_UI = [
    {
        "section": _("Workflows"),
        "fields": [
            dict(
                field="workflow",
                ui_widget="Dropdown",
                props=dict(
                    label=_("Default workflow"),
                    description=_("Default workflow for the community if "
                                  "workflow is not specified when depositing a record."),
                    options=lazy_workflow_options,
                ),
            ),
            dict(
                field="allowed_workflows",
                # todo: need to find a better widget for this
                ui_widget="MultiInput",
                props=dict(
                    label=_("Allowed workflows"),
                    description=_("Workflows allowed for the community."),
                    options=lazy_workflow_options,
                ),
            ),
        ],
    }
]
