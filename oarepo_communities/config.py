from invenio_communities.config import COMMUNITIES_ROUTES as INVENIO_COMMUNITIES_ROUTES
from oarepo_runtime.i18n import lazy_gettext as _

from .cf.workflows import WorkflowCF, lazy_workflow_options
from .notifications.generators import CommunityRoleEmailRecipient
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
                    description=_(
                        "Default workflow for the community if "
                        "workflow is not specified when depositing a record."
                    ),
                    options=lazy_workflow_options,
                ),
            ),
            dict(
                field="allowed_workflows",
                # todo: need to find a better widget for this
                ui_widget="Dropdown",
                props=dict(
                    label=_("Allowed workflows"),
                    multiple=True,
                    description=_("Workflows allowed for the community."),
                    options=lazy_workflow_options,
                ),
            ),
        ],
    }
]

COMMUNITIES_ROUTES = {**INVENIO_COMMUNITIES_ROUTES, "my_communities": "/me/communities"}

DISPLAY_USER_COMMUNITIES = True

DISPLAY_NEW_COMMUNITIES = True

NOTIFICATION_RECIPIENTS_RESOLVERS = {
    "community_role": {"email": CommunityRoleEmailRecipient}
}

DATASTREAMS_TRANSFORMERS = {
    "set_community": "oarepo_communities.datastreams.transformers.SetCommunityTransformer",
}
