#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF
from marshmallow import ValidationError
from marshmallow_utils.fields import SanitizedUnicode


class WorkflowField(SanitizedUnicode):
    def _validate(self, value: str) -> None:
        super()._validate(value)
        if value not in current_app.config["WORKFLOWS"]:
            raise ValidationError("Trying to set nonexistent workflow {value} on community.")


class WorkflowCF(KeywordCF):
    def __init__(self, name, field_cls=WorkflowField, **kwargs) -> None:
        """Constructor."""
        super().__init__(name, field_cls=field_cls, **kwargs)
