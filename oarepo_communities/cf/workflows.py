import enum

import marshmallow as ma
from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF


class WorkflowSchemaField(ma.fields.Enum):
    def __init__(self, **kwargs):
        enum_type = enum.Enum(
            'WorkflowEnum',
            {k: w.label for k, w in current_app.config["WORKFLOWS"].items()}
        )
        super().__init__(enum_type, **kwargs)


class WorkflowCF(KeywordCF):
    def __init__(self, name, **kwargs):
        super().__init__(name, field_cls=WorkflowSchemaField, **kwargs)


# hack to get lazy choices serialized to JSON
class LazyChoices(list):
    def __init__(self, func):
        self._func = func

    def __iter__(self):
        return iter(self._func())

    def __getitem__(self, item):
        return self._func()[item]

    def __len__(self):
        return len(self._func())


lazy_workflow_options = LazyChoices(
    lambda: [{'id': name, 'title_l10n': w.label} for name, w in current_app.config["WORKFLOWS"].items()]
)
