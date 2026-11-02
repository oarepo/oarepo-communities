# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Parameter for shared or my requests in communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_accounts.models import userrole
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

        role_ids = db.session.query(userrole.c.role_id).filter(userrole.c.user_id == identity.id).all()
        role_ids = [rid[0] for rid in role_ids]

        # this is just a filter, we can return a broader query that gets narrowed down in other filters
        # this could possibly be also done by receiver search grant checks; especially if we want all requests
        # the identity is receiver of
        return Bool(
            should=[
                ret,
                Q("terms", **{"receiver.community": community_ids}),
                Q("terms", **{"receiver.group": role_ids}),
            ],
        )
