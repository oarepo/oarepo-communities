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

from typing import TYPE_CHECKING, Any, cast, override

from invenio_rdm_records.services.schemas.parent.communities import CommunitiesSchema
from marshmallow import post_dump
from marshmallow_utils.fields import NestedAttribute
from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_rdm_records.services.schemas.parent import RDMParentSchema as InvenioRDMParentSchema
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
else:
    InvenioRDMParentSchema = object


class CommunitiesParentRecordSchemaMixin(InvenioRDMParentSchema):
    """Mixin for parent record schema."""

    # side effect of default = fields.String(attribute="default.id", allow_none=True) is that we need different
    # data loading in permissions (called before validation) and in schema (called after validation)
    # also iirc NestedAttribute caused issues in ui serialization
    communities = NestedAttribute(CommunitiesSchema)

    # RDMParentRecord already has this but it's called after the permission check
    @post_dump
    def _permissions_filter_dump(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        # Remove review before permission check
        if data.get("review") is None:
            data.pop("review", None)
        return cast("dict[str, Any]", super()._permissions_filter_dump(data, **kwargs))


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
        yield PrependMixin("ParentRecordSchema", CommunitiesParentRecordSchemaMixin)
