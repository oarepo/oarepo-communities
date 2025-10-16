#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for rdm functionality.

This module provides the RDMExtPreset that configures the main Flask extension
for handling records, resources, and services in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override
import marshmallow as ma
from invenio_rdm_records.services.pids import PIDManager, PIDsService
from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol

from marshmallow import Schema, fields

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder

# TODO: How to use RDM here? - invenio_rdm_records.services.schemas.parent.communities
class CommunitiesParentSchema(
    Schema
):
    ids = fields.List(fields.String())
    default = fields.String()

class CommunitiesParentRecordSchemaMixin:
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
