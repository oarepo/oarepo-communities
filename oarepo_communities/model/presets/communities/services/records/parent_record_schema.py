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

import marshmallow as ma
from marshmallow import Schema, fields
from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


# TODO: How to use RDM here? - invenio_rdm_records.services.schemas.parent.communities
class CommunitiesParentSchema(Schema):
    """Schema for communities field."""

    ids = fields.List(fields.String())
    default = fields.String()


class CommunitiesParentRecordSchemaMixin:
    """Mixin for parent record schema."""

    communities = ma.fields.Nested(CommunitiesParentSchema)


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
