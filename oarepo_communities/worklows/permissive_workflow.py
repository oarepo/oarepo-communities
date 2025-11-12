#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Permissive workflow for communities."""

from __future__ import annotations

from functools import partial

from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import AnyUser
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

# TODO: should this class be here? It seems that if needed, it should be in oarepo_workflows or oarepo_requests
# "default permissions" is already covered by oarepo_communities.services.permissions.policy.
# CommunityDefaultWorkflowPermissions
# and afaik we have no concrete workflows outside of tests or repository implementations anywhere


class PermissiveWorkflowPermissions(DefaultWorkflowPermissions):
    """Permissions for permissive workflow."""

    can_create = (PrimaryCommunityMembers(),)

    can_read = (
        RecordOwners(),
        IfInState(
            "published",
            then_=[AnyUser()],
        ),
    )

    can_update = (
        IfInState(
            "draft",
            then_=[
                RecordOwners(),
            ],
        ),
    )

    can_delete = (
        # draft can be deleted, published record must be deleted via request
        IfInState(
            "draft",
            then_=[
                RecordOwners(),
            ],
        ),
    )


class DefaultWorkflowRequests(WorkflowRequestPolicy):
    """Default requests for permissive workflow."""

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
    code="permissive",
    label="Permissive workflow",
    permission_policy_cls=PermissiveWorkflowPermissions,
    request_policy_cls=DefaultWorkflowRequests,
)
