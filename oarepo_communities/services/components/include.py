#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Community inclusion component."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_records_resources.services.records.components.base import ServiceComponent
from oarepo_runtime.typing import require_kwargs

from oarepo_communities.errors import MissingDefaultCommunityError

from ..permissions.generators import convert_community_ids_to_uuid

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_drafts_resources.records import Record

from invenio_drafts_resources.services.records.components.base import (
    BaseRecordFilesComponent,
)


class CommunityInclusionComponent(ServiceComponent):
    """Community inclusion component."""

    affects = (BaseRecordFilesComponent,)

    @override
    @require_kwargs("data", "record")
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        record: Record,
        **kwargs: Any,
    ) -> None:
        try:
            community_id = data["parent"]["communities"]["default"]["id"]
        except KeyError as exc:
            raise MissingDefaultCommunityError("Default community not defined in input.") from exc

        record.parent.communities.add(convert_community_ids_to_uuid(community_id), default=True)
