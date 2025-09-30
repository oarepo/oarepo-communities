#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Utility functions for communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import current_app, session
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities, current_identities_cache
from invenio_communities.utils import identity_cache_key
from invenio_records_resources.proxies import current_service_registry

from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.services.permissions.generators import UserInCommunityNeed

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_communities.members.records import Member as MemberRecord
    from invenio_drafts_resources.records import Record
    from invenio_records_resources.services.records.service import RecordService


def get_community_needs_for_identity(
    identity: Identity,
) -> list[tuple[str, str]] | None:
    """Get community needs for the given identity.

    Returns a list of (community_id, role) tuples or None if no user is logged in.
    """
    # see invenio_communities.utils.load_community_needs
    if identity.id is None:
        # no user is logged in
        return None

    cache_key = identity_cache_key(identity)
    community_roles = cast("list[tuple[str, str]] | None", current_identities_cache.get(cache_key))
    if community_roles is None:
        # aka Member.get_memberships(identity)
        roles_ids = session.get("unmanaged_roles_ids", [])

        member_cls = cast("MemberRecord", current_communities.service.members.config.record_cls)
        managed_community_roles = member_cls.get_memberships(identity)
        unmanaged_community_roles = member_cls.get_memberships_from_group_ids(identity, roles_ids)
        community_roles = managed_community_roles + unmanaged_community_roles

        current_identities_cache.set(
            cache_key,
            community_roles,
        )
    return community_roles


def load_community_user_needs(identity: Identity) -> None:
    """Load community needs for the given identity into its provides set."""
    community_roles = get_community_needs_for_identity(identity)
    if not community_roles:
        return
    communities = {community_role[0] for community_role in community_roles}
    needs = {UserInCommunityNeed(identity.id, community) for community in communities}
    identity.provides |= needs


# TODO: why is this needed?
def get_associated_service(record_service: RecordService, service_type: str) -> RecordService:
    """Get associated service for given record service and service type.

    The type might be, for example, files
    """
    return current_service_registry.get(f"{record_service.config.service_id}_{service_type}")


def slug2id(slug: str) -> str:
    """Convert community slug to id."""
    return str(current_communities.service.record_cls.pid.resolve(slug).id)


def get_record_services() -> dict[Record, RecordService]:
    """TODO: remove this to use the current runtime instead."""
    return {k: current_service_registry.get(v) for k, v in current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"].items()}


# TODO: why is this needed?
def get_service_by_urlprefix(url_prefix: str) -> RecordService:
    """Get service for given URL prefix."""
    return current_service_registry.get(current_oarepo_communities.urlprefix_serviceid_mapping[url_prefix])


# TODO: move to runtime
def get_service_from_schema_type(schema_type: str) -> RecordService:
    """Get service for given schema type."""
    for record_cls, service in get_record_services().items():
        if hasattr(record_cls, "schema") and record_cls.schema.value == schema_type:
            return service
    raise KeyError(f"No service found for schema type {schema_type}")


# TODO: why is this needed?
def get_urlprefix_service_id_mapping() -> dict[str, str]:
    """Get mapping of URL prefixes to service IDs."""
    ret = {}
    services = get_record_services().values()
    for service in services:
        if hasattr(service, "config") and hasattr(service.config, "url_prefix"):
            url_prefix = service.config.url_prefix.replace(
                "/", ""
            )  # this might be problematic bc idk if there's a reason for multiword prefix -
            # but that is a problem for using model view arg too
            ret[url_prefix] = service.config.service_id
    return ret


def community_id_from_record(record: Record) -> str | None:
    """Get community ID from record or its parent community."""
    if isinstance(record, Community):
        community_id = record.id
    else:
        record = record.parent if hasattr(record, "parent") else record
        try:
            community_id = record.communities.default.id
        except AttributeError:
            return None
    return community_id


def community_to_dict(community: Community) -> dict:
    """Convert community to dict suitable for embedding in record metadata."""
    return {
        "slug": str(community.slug),
        "id": str(community.id),
        "logo": f"/api/communities/{community.id}/logo",
        "links": {
            "self_html": f"/communities/{community.id}/records",
        },
        **(community.metadata or {}),
    }
