#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating parent record - community relationship metadata model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_communities.records.records.models import CommunityRelationMixin
from invenio_db import db
from oarepo_model.customizations import (
    AddBaseClasses,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ParentCommunityMetadataPreset(Preset):
    """Preset for draft record metadata class."""

    provides = ("ParentCommunityMetadata",)
    depends_on = ("ParentRecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("ParentCommunityMetadata")
        yield AddClassField(
            "ParentCommunityMetadata",
            "__tablename__",
            f"{builder.model.base_name}_parents_community",
        )
        yield AddClassField(
            "ParentCommunityMetadata",
            "__record_model__",
            dependencies["ParentRecordMetadata"],
        )
        yield AddBaseClasses("ParentCommunityMetadata", db.Model, CommunityRelationMixin)
