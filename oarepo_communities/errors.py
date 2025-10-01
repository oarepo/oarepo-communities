#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Configuration of the draft record requests resource."""

from __future__ import annotations

from typing import cast

from flask_resources import (
    create_error_handler,
)
from invenio_i18n import gettext as _
from marshmallow import ValidationError
from oarepo_requests.errors import CustomHTTPJSONException


class CommunityAlreadyIncludedError(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


class TargetCommunityNotProvidedError(Exception):
    """Target community not provided in the migration request."""

    description = "Target community not provided in the migration request."


class CommunityNotIncludedError(Exception):
    """The record is already in the community."""

    description = _("The record is not included in this community.")


class PrimaryCommunityError(Exception):
    """The record is already in the community."""

    description = _("Primary community can't be removed, can only be migrated to another.")


class MissingDefaultCommunityError(ValidationError):
    """Error raised when default community is missing."""

    description = _("Default community is not present in the input.")


class MissingCommunitiesError(ValidationError):
    """Error raised when communities are missing in the input data."""

    description = _("Communities are not present in the input.")


class CommunityDoesntExistError(ValidationError):
    """Error raised when the community specified in input data does not exist."""

    description = _("Input community does not exist.")


class CommunityAlreadyExistsError(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


class RecordCommunityMissingError(Exception):
    """Record does not belong to the community."""

    def __init__(self, record_id: str, community_id: str):
        """Initialise error."""
        self.record_id = record_id
        self.community_id = community_id

    @property
    def description(self) -> str:
        """Exception description."""
        return f"The record {self.record_id} in not included in the community {self.community_id}."


class OpenInclusionRequestAlreadyExistsError(Exception):
    """An open request already exists."""

    def __init__(self, request_id: str):
        """Initialize exception."""
        self.request_id = request_id

    @property
    def description(self) -> str:
        """Exception's description."""
        return cast("str", _("There is already an open inclusion request for this community."))  # mypy bug


RESOURCE_ERROR_HANDLERS = {
    CommunityAlreadyIncludedError: create_error_handler(
        lambda _e: CustomHTTPJSONException(
            code=400,
            description=_("The community is already included in the record."),
            request_payload_errors=[
                {
                    "field": "payload.community",
                    "messages": [_("Record is already in this community. Please choose another.")],
                }
            ],
        )
    ),
    TargetCommunityNotProvidedError: create_error_handler(
        lambda _e: CustomHTTPJSONException(
            code=400,
            description=_("Target community not provided in the migration request."),
            request_payload_errors=[
                {
                    "field": "payload.community",
                    "messages": [_("Please select the community")],
                }
            ],
        )
    ),
}
