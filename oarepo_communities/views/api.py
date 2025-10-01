#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Views for communities API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oarepo_communities.resolvers.communities import CommunityRoleResolver

if TYPE_CHECKING:
    from flask import Flask


# TODO: move this to finalizer, not record once as that has been removed
def register_community_role_entity_resolver_finalizer(
    app: Flask,
) -> None:  # TODO: consider using different method for registering the resolver
    """Register the community role entity resolver."""
    requests = app.extensions["invenio-requests"]
    requests.entity_resolvers_registry.register_type(CommunityRoleResolver())
