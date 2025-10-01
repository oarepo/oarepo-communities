#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Custom field for associating preferred and allowed workflows to a community."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from invenio_records_resources.services.custom_fields import KeywordCF
from marshmallow_utils.fields import SanitizedUnicode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def validate_workflow(code: str) -> bool:
    """Validate that the workflow with the given code exists."""
    return code in current_app.config["WORKFLOWS"]


class WorkflowSchemaField(SanitizedUnicode):
    """A custom Marshmallow field for validating workflow codes."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the field with a workflow validator."""
        super().__init__(validate=[validate_workflow], **kwargs)


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


# TODO: use current_workflows here
lazy_workflow_options = LazyChoices[dict[str, str]](
    lambda: [
        {"id": name, "title_l10n": w.label}  # type: ignore[]
        for name, w in current_app.config["WORKFLOWS"].items()  # type: ignore[]
    ]
)
"""A lazy list of available workflows for use in form choices."""
