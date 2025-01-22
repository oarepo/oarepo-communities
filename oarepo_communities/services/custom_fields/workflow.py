from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF
from marshmallow import ValidationError
from marshmallow_utils.fields import SanitizedUnicode


class WorkflowField(SanitizedUnicode):
    def _validate(self, value: str) -> None:
        super()._validate(value)
        if value not in current_app.config["WORKFLOWS"]:
            raise ValidationError(
                "Trying to set nonexistent workflow {value} on community."
            )


class WorkflowCF(KeywordCF):
    def __init__(self, name, field_cls=WorkflowField, **kwargs) -> None:
        """Constructor."""
        super().__init__(name, field_cls=field_cls, **kwargs)
