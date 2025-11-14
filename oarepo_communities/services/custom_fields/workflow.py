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

from flask_babel import LazyString
from invenio_records_resources.services.custom_fields import KeywordCF
from marshmallow_utils.fields import SanitizedUnicode
from oarepo_workflows import current_oarepo_workflows

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class WorkflowSchemaField(SanitizedUnicode):
    """A custom Marshmallow field for validating workflow codes."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the field with a workflow validator."""
        super().__init__(validate=[lambda code: code in current_oarepo_workflows.workflow_by_code], **kwargs)


class WorkflowCF(KeywordCF):
    """A custom field for associating preferred and allowed workflows to a community."""

    def __init__(self, name: str, **kwargs: Any) -> None:
        """Initialize the custom field with a specific Marshmallow field for workflow validation."""
        super().__init__(name, field_cls=WorkflowSchemaField, **kwargs)


class LazyChoices[T](list[T]):
    """Invenio uses default JSON encoder which does not support lazy objects, such as localized strings.

    This class wraps a callable returning a list and implements list interface to make it JSON serializable.
    """

    def __init__(self, func: Callable[[], list[T]]) -> None:
        """Initialize the lazy choices with a callable."""
        self._func = func

    @override
    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the choices."""
        return iter(self._func())

    @override
    def __getitem__(self, item: int) -> T:  # type: ignore[override]
        return self._func()[item]

    @override
    def __len__(self) -> int:
        return len(self._func())


lazy_workflow_options = LazyChoices[dict[str, str | LazyString]](
    lambda: [{"id": name, "title_l10n": w.label} for name, w in current_oarepo_workflows.workflow_by_code.items()]
)
