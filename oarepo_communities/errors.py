#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Configuration of the draft record requests resource."""

from __future__ import annotations

import json
from typing import Any, Optional, Union

from flask import g
from flask_resources import (
    HTTPJSONException,
    create_error_handler,
)
from flask_resources.serializers.json import JSONEncoder
from marshmallow import ValidationError
from oarepo_runtime.i18n import lazy_gettext as _


class CustomHTTPJSONException(HTTPJSONException):
    """Custom HTTP Exception delivering JSON error responses with an error_type."""

    def __init__(
        self,
        code: Optional[int] = None,
        errors: Optional[Union[dict[str, any], list]] = None,
        error_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize CustomHTTPJSONException."""
        super().__init__(code=code, errors=errors, **kwargs)
        self.error_type = error_type  # Save the error_type passed in the constructor

    def get_body(self, environ: any = None, scope: any = None) -> str:
        """Get the request body."""
        body = {"status": self.code, "message": self.get_description(environ)}

        errors = self.get_errors()
        if errors:
            body["errors"] = errors

        # Add error_type to the response body
        if self.error_type:
            body["error_type"] = self.error_type

        # TODO: Revisit how to integrate error monitoring services. See issue #56
        # Temporarily kept for expediency and backward-compatibility
        if self.code and (self.code >= 500) and hasattr(g, "sentry_event_id"):
            body["error_id"] = str(g.sentry_event_id)

        return json.dumps(body, cls=JSONEncoder)


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
            errors=[
                {
                    "field": "payload.community",
                    "messages": [
                        _("Record is already in this community. Please choose another.")
                    ],
                }
            ],
            error_type="cf_validation_error",
        )
    ),
    TargetCommunityNotProvidedException: create_error_handler(
        lambda e: CustomHTTPJSONException(
            code=400,
            description=_("Target community not provided in the migration request."),
            errors=[
                {
                    "field": "payload.community",
                    "messages": [_("Please select the community")],
                }
            ],
            error_type="cf_validation_error",
        )
    ),
}
