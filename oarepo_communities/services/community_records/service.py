#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Community records service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.base.service import Service
from invenio_search.engine import dsl

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_communities.communities.records.api import Community
    from invenio_records_resources.services.records.results import RecordList


class CommunityRecordsService(Service):
    """Community records service.

    The record communities service is in charge of managing the records of a given community.
    """

    @property
    def community_cls(self) -> type[Community]:
        """Factory for creating a community class."""
        return self.config.community_cls  # type: ignore[no-any-return]

    def search(
        self,
        identity: Identity,
        community_id: str,
        params: dict[str, Any] | None = None,
        search_preference: str | None = None,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Search for records published in the given community."""
        self.require_permission(identity, "search")

        community = self.community_cls.pid.resolve(community_id)  # Ensure community's existence

        params = params or {}

        # A single community may be designated as the "collections community" — a
        # holder for cross-repository (non-community-scoped) collection trees. When
        # searching through that community we skip the community_filter so a
        # collection's own search_query resolves against every published record,
        # not only records tagged with the holder community. Compare against the
        # resolved community's slug — the caller may pass either slug or UUID as
        # community_id.
        collections_community_slug = current_app.config.get("INVENIO_COLLECTIONS_COMMUNITY_SLUG")
        is_collections_community = (
            collections_community_slug is not None and community.slug == collections_community_slug  # pyright: ignore[reportAttributeAccessIssue]
        )

        if is_collections_community:
            search_filter = extra_filter
        else:
            community_filter = dsl.Q("term", **{"parent.communities.ids": str(community.id)})
            search_filter = community_filter & extra_filter if extra_filter is not None else community_filter

        return current_rdm_records_service.search(
            identity,
            params=params,
            search_preference=search_preference,
            extra_filter=search_filter,
            **kwargs,
        )
