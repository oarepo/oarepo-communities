# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module for communities related notifications functionality."""

from __future__ import annotations

from invenio_records_resources.references.entity_resolvers import ServiceResultResolver


def community_role_notification_resolver() -> ServiceResultResolver:
    """Return community role notification resolver."""
    return ServiceResultResolver(service_id="community-role", type_key="community_role")


# due to how invenio notifications resolves this as entrypoint
community_role_notification_resolver.type_key = "community_role"  # ty: ignore[missing-attribute]
