#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Community submission request type with custom accept action."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from invenio_rdm_records.requests.community_submission import (
    AcceptAction as InvenioAcceptAction,
)
from invenio_rdm_records.requests.community_submission import (
    CommunitySubmission as InvenioCommunitySubmission,
)
from oarepo_requests.services.permissions.identity import request_active
from oarepo_requests.utils import classproperty

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_requests import RequestAction


# TODO: move directly to invenio/oarepo service
class AcceptAction(InvenioAcceptAction):
    """Accept action that grants request_active permission during execution."""

    def execute(self, identity: Identity, uow: UnitOfWork, **kwargs: Any) -> None:
        """Execute the accept action with request_active added to identity.

        This is needed because publishing through workflows is done by requests.
        """
        identity.provides.add(request_active)
        try:
            super().execute(identity, uow, **kwargs)
        finally:
            identity.provides.remove(request_active)


class CommunitySubmission(InvenioCommunitySubmission):
    """Community submission request type using dynamic model-based topic ref types and custom accept action."""

    allowed_topic_ref_types = ["record"]  # type: ignore[reportAssignmentType]
    allowed_receiver_ref_types = (
        *InvenioCommunitySubmission.allowed_receiver_ref_types,
        "community_role",
        "auto_approve",
    )

    @classproperty
    @override
    def available_actions(  # type: ignore[override]
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": AcceptAction,
        }
