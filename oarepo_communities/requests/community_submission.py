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

from typing import TYPE_CHECKING, cast, override

from invenio_access.permissions import system_identity
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_rdm_records.checks.requests import (
    SubmissionCancelAction,
    SubmissionCreateAction,
)
from invenio_rdm_records.requests.community_submission import (
    AcceptAction as InvenioAcceptAction,
)
from invenio_rdm_records.requests.community_submission import (
    CancelAction as InvenioCancelAction,
)
from invenio_rdm_records.requests.community_submission import (
    CommunitySubmission as InvenioCommunitySubmission,
)
from invenio_rdm_records.requests.community_submission import (
    DeclineAction as InvenioDeclineAction,
)
from invenio_rdm_records.requests.community_submission import (
    ExpireAction as InvenioExpireAction,
)
from invenio_records_resources.services.uow import RecordIndexOp
from invenio_requests.proxies import current_requests_service
from oarepo_requests.services.permissions.identity import request_active
from oarepo_requests.utils import classproperty
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_drafts_resources.records import Record
    from invenio_requests import RequestAction
    from invenio_requests.records.api import Request


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


def _reopen_review(closed_request: Request, draft: Record, uow: UnitOfWork) -> None:
    """Replace a closed review with a fresh open one on the same community.

    Invenio's ``DeclineAction``/``ExpireAction`` keep the closed request attached
    as ``parent.review`` and ``CancelAction`` detaches it entirely. Either way the
    draft can no longer be submitted for review to the same community: the former
    leaves ``record.status`` at ``declined``/``expired`` (the submit button is
    hidden), the latter drops the community selection.

    Instead, we create a brand-new ``community-submission`` request in the
    ``created`` state for the same community and re-attach it as ``parent.review``.
    This puts the draft back into ``draft_with_review`` -- the exact state it was
    in before the review was submitted -- so the community stays selected and the
    submit-for-review button is shown again. The original closed request is kept
    in the requests list, preserving the decline/cancel/expire history.

    The new request is created as ``system_identity`` (so the acting curator does
    not need requester permission) but attributed to the original submitter via
    ``creator``. A community-submission review always lives on ``parent.review``
    (new-version reviews on ``draft.review`` are not created for this type), so
    only the parent review is handled.
    """
    community = closed_request.receiver.resolve()
    creator = closed_request.created_by.resolve()

    # Detach the closed request (a no-op for cancel, which already detached it)
    # so the review service does not reject the new request as a duplicate.
    if draft.parent.review is not None:
        draft.parent.review = None

    request_item = current_requests_service.create(
        system_identity,
        data={},
        request_type=closed_request.type,
        receiver=community,
        creator=creator,
        topic=draft,
        uow=uow,
    )

    # ``request_item._request`` mirrors invenio's own ``ReviewService.create``:
    # the systemfield needs the actual Request record (not just its id) so the
    # optimistic-concurrency version can be dumped without a lazy re-fetch during
    # commit, and ``RequestItem`` exposes no public accessor for it.
    draft.parent.review = request_item._request  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]

    # Resolve the model-specific service (datarepo records are a custom model, not
    # vanilla RDM) so the parent commit reindexes the draft and its siblings with
    # the correct record/draft classes and indexers -- as requests/utils.py does.
    record_service = current_runtime.get_record_service_for_record(draft)
    uow.register(ParentRecordCommitOp(draft.parent, indexer_context={"service": record_service}))
    # index_refresh mirrors the request-flow indexing in requests/utils.py so the
    # reopened review is immediately visible to the deposit form reload.
    uow.register(
        RecordIndexOp(
            draft,
            indexer=record_service.draft_indexer,  # pyright: ignore[reportAttributeAccessIssue]
            index_refresh=True,
        )
    )


class DeclineAction(InvenioDeclineAction):
    """Decline action that reopens a fresh review so the record can be resubmitted."""

    def execute(self, identity: Identity, uow: UnitOfWork, **kwargs: Any) -> None:
        """Decline the request, then reopen a fresh review on the same community."""
        draft = self.request.topic.resolve()
        super().execute(identity, uow, **kwargs)
        _reopen_review(self.request, draft, uow)


class ExpireAction(InvenioExpireAction):
    """Expire action that reopens a fresh review so the record can be resubmitted."""

    def execute(self, identity: Identity, uow: UnitOfWork, **kwargs: Any) -> None:
        """Expire the request, then reopen a fresh review on the same community."""
        draft = self.request.topic.resolve()
        super().execute(identity, uow, **kwargs)
        _reopen_review(self.request, draft, uow)


# InvenioCancelAction (the dynamic base of SubmissionCancelAction) is listed
# explicitly so type checkers can resolve ``self.request`` on this action; it is
# already the runtime base, so the MRO is unchanged.
class CancelAction(SubmissionCancelAction, InvenioCancelAction):
    """Cancel action that reopens a fresh review so the record can be resubmitted."""

    def execute(self, identity: Identity, uow: UnitOfWork, **kwargs: Any) -> None:
        """Cancel the request, then reopen a fresh review on the same community."""
        draft = self.request.topic.resolve()
        super().execute(identity, uow, **kwargs)
        _reopen_review(self.request, draft, uow)


class CommunitySubmission(InvenioCommunitySubmission):
    """Community submission request type using dynamic model-based topic ref types and custom accept action."""

    @classproperty
    @override
    def available_actions(  # type: ignore[override]
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        # The check-integration and reopen actions have dynamically-computed base
        # classes that type checkers cannot trace back to RequestAction, so the
        # dict is cast to the declared return type.
        return cast(
            "dict[str, type[RequestAction]]",
            {
                **super().available_actions,
                "accept": AcceptAction,
                "create": SubmissionCreateAction,
                "cancel": CancelAction,
                "decline": DeclineAction,
                "expire": ExpireAction,
            },
        )
