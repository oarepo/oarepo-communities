#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Configuration of the draft record requests resource."""

from __future__ import annotations


from flask_resources import (
    create_error_handler,
)
from marshmallow import ValidationError
from oarepo_runtime.i18n import lazy_gettext as _
from oarepo_requests.errors import CustomHTTPJSONException


class CommunityAlreadyIncludedException(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


class TargetCommunityNotProvidedException(Exception):
    """Target community not provided in the migration request"""

    description = "Target community not provided in the migration request."


class CommunityNotIncludedException(Exception):
    """The record is already in the community."""

    description = _("The record is not included in this community.")


class PrimaryCommunityException(Exception):
    """The record is already in the community."""

    description = _(
        "Primary community can't be removed, can only be migrated to another."
    )


class MissingDefaultCommunityError(ValidationError):
    """"""

    description = _("Default community is not present in the input.")


class MissingCommunitiesError(ValidationError):
    """"""

    description = _("Communities are not present in the input.")


class CommunityDoesntExistError(ValidationError):
    """"""

    description = _("Input community does not exist.")


class CommunityAlreadyExists(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


class RecordCommunityMissing(Exception):
    """Record does not belong to the community."""

    def __init__(self, record_id: str, community_id: str):
        """Initialise error."""
        self.record_id = record_id
        self.community_id = community_id

    @property
    def description(self) -> str:
        """Exception description."""
        return "The record {record_id} in not included in the community {community_id}.".format(
            record_id=self.record_id, community_id=self.community_id
        )


class OpenRequestAlreadyExists(Exception):
    """An open request already exists."""

    def __init__(self, request_id: str):
        """Initialize exception."""
        self.request_id = request_id

    @property
    def description(self) -> str:
        """Exception's description."""
        return _("There is already an open inclusion request for this community.")


RESOURCE_ERROR_HANDLERS = {
    CommunityAlreadyIncludedException: create_error_handler(
        lambda e: CustomHTTPJSONException(
            code=400,
            description=_("The community is already included in the record."),
            request_payload_errors=[
                {
                    "field": "payload.community",
                    "messages": [
                        _("Record is already in this community. Please choose another.")
                    ],
                }
            ],
        )
    ),
    TargetCommunityNotProvidedException: create_error_handler(
        lambda e: CustomHTTPJSONException(
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
