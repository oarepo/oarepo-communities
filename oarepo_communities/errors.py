#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Configuration of the draft record requests resource."""

from __future__ import annotations

from flask_babelex import lazy_gettext as _
from marshmallow import ValidationError

import json
from typing import Any, Dict, Optional, Union

from flask import g
from flask_resources import (
    HTTPJSONException,
    create_error_handler,
)
from flask_resources.serializers.json import JSONEncoder

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


def community_already_included_entry():
    """Entry point for CommunityAlreadyIncludedException handler."""
    return (
        CommunityAlreadyIncludedException,
        create_error_handler(
            lambda e: CustomHTTPJSONException(
                code=400,
                description="The community is already included in the record.",
                errors=[
                    {
                        "field": "payload.community",
                        "messages": [
                            "Record is already in this community. Please choose another."
                        ],
                    }
                ],
                error_type="cf_validation_error",
            )
        ),
    )


def target_community_not_provided_entry():
    """Entry point for TargetCommunityNotProvidedException handler."""
    return (
        TargetCommunityNotProvidedException,
        create_error_handler(
            lambda e: CustomHTTPJSONException(
                code=400,
                description="Target community not provided in the migration request.",
                errors=[
                    {
                        "field": "payload.community",
                        "messages": ["Please select the community"],
                    }
                ],
                error_type="cf_validation_error",
            )
        ),
    )


class CommunityAlreadyIncludedException(Exception):
    """The record is already in the community."""

    description = "The record is already included in this community."


class TargetCommunityNotProvidedException(Exception):
    """Target community not provided in the migration request"""

    description = "Target community not provided in the migration request."


class CommunityNotIncludedException(Exception):
    """The record is already in the community."""

    description = "The record is not included in this community."


class PrimaryCommunityException(Exception):
    """The record is already in the community."""

    description = "Primary community can't be removed, can only be migrated to another."


class MissingDefaultCommunityError(ValidationError):
    """"""


class MissingCommunitiesError(ValidationError):
    """"""


class CommunityAlreadyExists(Exception):
    """The record is already in the community."""

    description = "The record is already included in this community."


class RecordCommunityMissing(Exception):
    """Record does not belong to the community."""

    def __init__(self, record_id, community_id):
        """Initialise error."""
        self.record_id = record_id
        self.community_id = community_id

    @property
    def description(self):
        """Exception description."""
        return "The record {record_id} in not included in the community {community_id}.".format(
            record_id=self.record_id, community_id=self.community_id
        )


class OpenRequestAlreadyExists(Exception):
    """An open request already exists."""

    def __init__(self, request_id):
        """Initialize exception."""
        self.request_id = request_id

    @property
    def description(self):
        """Exception's description."""
        return _("There is already an open inclusion request for this community.")
