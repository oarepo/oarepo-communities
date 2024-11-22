from functools import partial

from invenio_records_permissions.generators import AnyUser
from oarepo_runtime.services.permissions.generators import RecordOwners
from oarepo_workflows import (
    AutoApprove,
    IfInState,
    Workflow,
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)
from oarepo_workflows.services.permissions import DefaultWorkflowPermissions

from oarepo_communities.services.permissions.generators import PrimaryCommunityMembers


class PermissiveWorkflowPermissions(DefaultWorkflowPermissions):
    can_create = [PrimaryCommunityMembers()]

    can_read = [
        RecordOwners(),
        IfInState(
            "published",
            then_=[AnyUser()],
        ),
    ]

    can_update = [
        IfInState(
            "draft",
            then_=[
                RecordOwners(),
            ],
        ),
    ]

    can_delete = [
        # draft can be deleted, published record must be deleted via request
        IfInState(
            "draft",
            then_=[
                RecordOwners(),
            ],
        ),
    ]


class DefaultWorkflowRequests(WorkflowRequestPolicy):
    publish_draft = WorkflowRequest(
        # if the record is in draft state, the owner or curator can request publishing
        requesters=[IfInState("draft", then_=[RecordOwners()])],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(accepted="published"),
    )

    edit_published_record = WorkflowRequest(
        requesters=[
            IfInState(
                "published",
                then_=[
                    RecordOwners(),
                ],
            )
        ],
        recipients=[AutoApprove()],
    )

    delete_published_record = WorkflowRequest(
        requesters=[
            IfInState(
                "published",
                then_=[
                    RecordOwners(),
                ],
            )
        ],
        recipients=[AutoApprove()],
        transitions=WorkflowTransitions(accepted="deleted"),
    )


PermissiveWorkflow = partial(
    Workflow,
    label="Permissive workflow",
    permission_policy_cls=PermissiveWorkflowPermissions,
    request_policy_cls=DefaultWorkflowRequests,
)
