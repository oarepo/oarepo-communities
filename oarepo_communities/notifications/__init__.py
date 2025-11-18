#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module for communities related notifications functionality."""

from __future__ import annotations

from invenio_records_resources.references.entity_resolvers import ServiceResultResolver


def community_role_notification_resolver() -> ServiceResultResolver:
    """Return community role notification resolver."""
    return ServiceResultResolver(service_id="community-role", type_key="community_role")


community_role_notification_resolver.type_key = "community_role"  # type: ignore[attr-defined]
