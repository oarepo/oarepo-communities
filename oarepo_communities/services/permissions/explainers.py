#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Permission explainers for community permission generators."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, cast, override

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from oarepo_runtime.services.permission_explainer import (
    ExplainerResult,
    PermissionExplainer,
    explain,
)

from oarepo_communities.services.permissions.generators import InAnyCommunity, OARepoCommunityRoles

if TYPE_CHECKING:
    from flask_principal import Identity


class InAnyCommunityPermissionExplainer(PermissionExplainer):
    """Explainer for InAnyCommunity permission generator."""

    TYPES = (InAnyCommunity,)

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        ret = super().explain(identity)
        generator = cast("InAnyCommunity", self.generator)
        over = self.permission_policy.over

        data = over.get("data")
        data = {**data} if data is not None else {}
        if "parent" in data:
            data["parent"] = copy.deepcopy(data["parent"])
        else:
            data["parent"] = {}

        for community in db.session.query(CommunityMetadata).all():
            data["parent"]["communities"] = {"default": str(community.id)}
            community_over = {**over, "data": data, "community_metadata": community}
            community_policy = type(self.permission_policy)(self.permission_policy.action, **community_over)
            ret.append(
                [
                    f"community: {community.slug}",
                    explain(identity, community_policy, generator.permission_generator),
                ]
            )
        return ret


class CommunityRolePermissionExplainer(PermissionExplainer):
    """Explainer for OARepoCommunityRoles permission generators (CommunityRole, DefaultCommunityRole, ...)."""

    TYPES = (OARepoCommunityRoles,)

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        ret = super().explain(identity)
        generator = cast("OARepoCommunityRoles", self.generator)
        ret.append(f"  - roles: {generator.roles(**self.permission_policy.over)}")
        return ret
