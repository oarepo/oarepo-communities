#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Workflow custom field for communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF
from marshmallow import ValidationError
from marshmallow_utils.fields import SanitizedUnicode

if TYPE_CHECKING:
    from marshmallow.fields import Field


class WorkflowField(SanitizedUnicode):
    """Workflow marshmallow field."""

    @override
    def _validate(self, value: str) -> None:
        """Validate the workflow exists."""
        super()._validate(value)
        if value not in current_app.config["WORKFLOWS"]:
            raise ValidationError("Trying to set nonexistent workflow {value} on community.")


class WorkflowCF(KeywordCF):
    """Workflow custom field."""

    def __init__(self, name: str, field_cls: type[Field] = WorkflowField, **kwargs: Any) -> None:
        """Create the workflow custom field."""
        super().__init__(name, field_cls=field_cls, **kwargs)
