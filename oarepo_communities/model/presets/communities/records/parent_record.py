# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for modifying parent record to support communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_communities.records.records.systemfields import CommunitiesField
from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CommunitiesParentRecordPreset(Preset):
    """Preset for record service class."""

    depends_on = ("ParentCommunityMetadata",)
    modifies = ("ParentRecord",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class CommunitiesParentRecordMixin:
            communities = CommunitiesField(dependencies["ParentCommunityMetadata"])

        yield PrependMixin("ParentRecord", CommunitiesParentRecordMixin)
