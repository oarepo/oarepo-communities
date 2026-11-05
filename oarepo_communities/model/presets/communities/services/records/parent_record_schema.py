# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Extension preset for additional communities related parent record schema fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from marshmallow import post_dump
from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_rdm_records.services.schemas.parent import (
        RDMParentSchema as InvenioRDMParentSchema,
    )
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
else:
    InvenioRDMParentSchema = object


class CommunitiesParentRecordSchemaMixin(InvenioRDMParentSchema):
    """Mixin for parent record schema."""

    # CleanReviewMixin post_dump in the parent is called after FieldPermissionsMixin's post_dump
    # it doesn't crash now but still prevents unnecessary permission checks
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
