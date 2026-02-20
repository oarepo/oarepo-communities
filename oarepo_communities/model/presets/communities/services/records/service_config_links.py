#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring RDM service config links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.config import (
    is_draft_and_has_review,
)
from invenio_records_resources.services.records.links import (
    RecordEndpointLink,
)
from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.presets import Preset
from oarepo_runtime.services.config import (
    has_permission,
    is_published_record,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CommunitiesServiceConfigLinks(Preset):
    """Preset for extra RDM service config links."""

    modifies = ("record_links_item",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToDictionary(
            "record_links_item",
            {
                "review": RecordEndpointLink(
                    "records.review_read",
                    when=not is_published_record() & has_permission("review"),
                ),
                "submit-review": RecordEndpointLink(
                    "records.review_submit",
                    when=is_draft_and_has_review,
                ),
            },
        )
