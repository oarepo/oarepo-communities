#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing permission policy for records in communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_permissions.policies.records import RecordPermissionPolicy
from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

from oarepo_communities.services.permissions.policy import (
    CommunityWorkflowPermissionPolicy,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CommunitiesPermissionPolicyPreset(Preset):
    """Preset for communities permissions class."""

    modifies = ("PermissionPolicy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "PermissionPolicy",
            RecordPermissionPolicy,
            CommunityWorkflowPermissionPolicy,
            subclass=True,
        )
