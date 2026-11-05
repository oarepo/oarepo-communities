# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Parameter for shared or my requests in communities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_records_resources.references import EntityGrant
from invenio_requests.services.requests.config import SharedOrMyRequestsParam
from opensearch_dsl.query import Bool, Q

if TYPE_CHECKING:
    from flask_principal import Identity


class CommunitiesSharedOrMyRequestsParam(SharedOrMyRequestsParam):
    """Param interpreter that includes community roles in /api/users/requests API."""

    @override
    def _generate_my_requests_query(self, identity: Identity) -> Bool:
        ret = super()._generate_my_requests_query(identity)
        needs = identity.provides  # actions needs aren't here and support is not implemented for now
        receiver_grants = [EntityGrant("receiver", need).token for need in needs]
        return Bool(
            should=[
                ret,
                Q("terms", grants=receiver_grants),
            ],
        )
