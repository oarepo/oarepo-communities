#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Parameter for shared or my requests in communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_communities.members.records.models import MemberModel
from invenio_db import db
from invenio_requests.services.requests.config import SharedOrMyRequestsParam
from opensearch_dsl.query import Bool, Q

if TYPE_CHECKING:
    from flask_principal import Identity


class CommunitiesSharedOrMyRequestsParam(SharedOrMyRequestsParam):
    """Param interpreter that includes community roles in /api/users/requests API."""

    @override
    def _generate_my_requests_query(self, identity: Identity) -> Bool:
        ret = super()._generate_my_requests_query(identity)

        # check community roles of the given identity
        community_ids = db.session.query(MemberModel.community_id).filter(MemberModel.user_id == identity.id).all()
        community_ids = [cid[0] for cid in community_ids]

        # this is just a filter, we can return a broader query that gets narrowed down in other filters
        return Bool(
            should=[
                ret,
                Q("terms", **{"receiver.community": community_ids}),
            ],
        )
