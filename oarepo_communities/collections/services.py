# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Records service backing the community collections service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from oarepo_rdm.services.service import OARepoCommunityRecordsService

if TYPE_CHECKING:
    from invenio_access.permissions import Identity
    from invenio_records_resources.services.records.results import RecordList


class GlobalCollectionsRecordsService(OARepoCommunityRecordsService):
    """Community records service used by collections.

    Behaves like the community-scoped multiplexed search, except for the
    global-collections community (``COLLECTIONS_COMMUNITY_SLUG``),
    whose collections search across every record instead of only records
    tagged with the holder community.
    """

    @override
    def search(
        self,
        identity: Identity,
        community_id: str,
        params: dict[str, Any] | None = None,
        search_preference: str | None = None,
        extra_filter: Any | None = None,
        scan: bool = False,
        scan_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Search a community's records, unscoped for the global-collections community."""
        slug = current_app.config.get("COLLECTIONS_COMMUNITY_SLUG")
        if slug is not None:
            community = self.community_cls.pid.resolve(community_id)
            if community.slug == slug:
                return current_rdm_records_service.search(
                    identity,
                    params=params or {},
                    search_preference=search_preference,
                    extra_filter=extra_filter,
                    **kwargs,
                )
        return super().search(
            identity,
            community_id,
            params,
            search_preference,
            extra_filter,
            scan,
            scan_params,
            **kwargs,
        )
