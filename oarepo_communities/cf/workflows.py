from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF

if TYPE_CHECKING:
    from typing import Any


def validate_workflow(value: str) -> bool:
    return value in current_app.config["WORKFLOWS"]


class WorkflowSchemaField(ma.fields.Str):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(validate=[validate_workflow], **kwargs)


class WorkflowCF(KeywordCF):
    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(name, field_cls=WorkflowSchemaField, **kwargs)


# hack to get lazy choices serialized to JSON
class LazyChoices(list):
    def __init__(self, func: callable):
        self._func = func

    def __iter__(self):
        return iter(self._func())

    def __getitem__(self, item):
        return self._func()[item]

    def __len__(self):
        return len(self._func())


lazy_workflow_options = LazyChoices(
    lambda: [
        {"id": name, "title_l10n": w.label}
        for name, w in current_app.config["WORKFLOWS"].items()
    ]
)
