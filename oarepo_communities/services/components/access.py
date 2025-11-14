#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Record access component for communities service.

This component is responsible for setting access on records based on the access
defined by the community. If the community is public, nothing is done.
If the community is private, the record's access is set to restricted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_drafts_resources.records.api import Record as RecordWithParent
from invenio_rdm_records.records.systemfields.access.protection import Visibility
from invenio_records_resources.services.records.components.base import ServiceComponent

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_records_resources.records.api import Record


class CommunityRecordAccessComponent(ServiceComponent):
    """Component setting record access field based on the community's access."""

    # affects all components, so should be placed as the first one
    depends_on = "*"

    @override
    def create(
        self,
        identity: Identity,
        data: dict[str, Any] | None = None,
        record: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Set access on the record based on the community's access."""
        if record is None:
            raise ValueError("record is required when creating a record")  # pragma: no cover

        if not isinstance(record, RecordWithParent):
            raise TypeError("record must be an instance of draft or published record with parent")  # pragma: no cover

        community = record.parent.communities.default
        if community and community.access.visibility_is_restricted:
            access = getattr(record, "access", None)
            if access is None:
                raise ValueError("record must have access field")  # pragma: no cover
            access.protection.record = Visibility.RESTRICTED
