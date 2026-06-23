#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A helper function to get the default workflow for a community.

This function is registered in oarepo_workflows and is used to get the default workflow
from the community id inside the record's metadata.
"""

from __future__ import annotations

from typing import cast

from flask import current_app
from oarepo_workflows import Workflow, current_oarepo_workflows
from oarepo_workflows.errors import InvalidWorkflowError


def get_workflow_from_community_custom_fields(custom_fields: dict) -> Workflow:
    """Get workflow from community custom fields."""
    workflow_id = custom_fields.get(
        "workflow",
        current_app.config["WORKFLOWS_DEFAULT_WORKFLOW"],
    )
    if not workflow_id and current_app.config.get("OAREPO_COMMUNITIES_DEFAULT_WORKFLOW", None):
        workflow_id = current_app.config["OAREPO_COMMUNITIES_DEFAULT_WORKFLOW"]
    try:
        return current_oarepo_workflows.workflow_by_code[workflow_id]
    except KeyError:
        raise InvalidWorkflowError(f"Workflow {workflow_id} does not exist in the configuration.") from None


def get_allowed_workflows(custom_fields: dict) -> list[str]:
    """Get allowed workflows for the given community."""
    allowed_workflows = custom_fields.get("allowed_workflows", [])
    if allowed_workflows:
        return allowed_workflows
    if current_app.config.get("OAREPO_COMMUNITIES_DEFAULT_WORKFLOW"):
        return [cast("str", current_app.config.get("OAREPO_COMMUNITIES_DEFAULT_WORKFLOW"))]
    return []
