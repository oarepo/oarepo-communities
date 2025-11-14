#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Extension preset for additional communities related parent record schema fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.schemas.parent.communities import CommunitiesSchema
from marshmallow_utils.fields import NestedAttribute
from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CommunitiesParentRecordSchemaMixin:
    """Mixin for parent record schema."""

    # side effect of default = fields.String(attribute="default.id", allow_none=True) is that we need different
    # data loading in permissions (called before validation) and in schema (called after validation)
    # also iirc NestedAttribute caused issues in ui serialization
    communities = NestedAttribute(CommunitiesSchema)


class CommunitiesParentRecordSchemaPreset(Preset):
    """Preset for extension class."""

    modifies = ("ParentRecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddMixins("ParentRecordSchema", CommunitiesParentRecordSchemaMixin)
