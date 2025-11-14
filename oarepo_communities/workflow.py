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

from typing import TYPE_CHECKING, cast

from flask import current_app
from invenio_communities.communities.records.api import Community
from invenio_pidstore.errors import PIDDoesNotExistError
from oarepo_workflows import Workflow, current_oarepo_workflows

from oarepo_communities.errors import (
    CommunityDoesntExistError,
    MissingDefaultCommunityError,
)
from oarepo_communities.utils import community_id_from_record

if TYPE_CHECKING:
    from typing import Any


def community_default_workflow(**kwargs: Any) -> Workflow:
    """Get default workflow for the community."""
    # optimization: if community metadata is passed, use it
    if "community_metadata" in kwargs:
        community_metadata = kwargs["community_metadata"]
        return get_workflow_from_community_custom_fields(community_metadata.json.get("custom_fields", {}))

    if "record" not in kwargs and "data" not in kwargs:  # nothing to get community from
        raise MissingDefaultCommunityError("Can't get community when neither record nor input data are present.")

    community_id: str | None
    if "record" in kwargs:
        community_id = community_id_from_record(kwargs["record"])
    else:
        try:
            community_id = kwargs["data"]["parent"]["communities"]["default"]["id"]
        except (KeyError, TypeError):
            try:
                community_id = kwargs["data"]["parent"]["communities"]["default"]
            except KeyError as e:
                raise MissingDefaultCommunityError("Failed to get community from input data.") from e

    if community_id is None:
        raise MissingDefaultCommunityError("Failed to get community from record.")

    # use pid resolve so that the community might be both slug or id
    try:
        community = cast("Community", Community.pid.resolve(community_id))
    except PIDDoesNotExistError as e:
        raise CommunityDoesntExistError(community_id) from e

    return get_workflow_from_community_custom_fields(community.custom_fields)


def get_workflow_from_community_custom_fields(custom_fields: dict) -> Workflow:
    """Get workflow from community custom fields."""
    workflow_id = custom_fields.get(
        "workflow",
        current_app.config["OAREPO_COMMUNITIES_DEFAULT_WORKFLOW"],
    )
    return current_oarepo_workflows.workflow_by_code[workflow_id]
