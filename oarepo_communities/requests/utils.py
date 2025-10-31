#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Utility functions for requests in communities."""

from __future__ import annotations

# TODO: this file needs to be moved to oarepo_requests
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.uow import RecordIndexOp
from oarepo_requests.utils import (
    is_auto_approved,
    request_identity_matches,
)
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_communities.communities.records.api import Community
    from invenio_db.uow import UnitOfWork
    from invenio_drafts_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType
    from invenio_requests.records.api import Request


def auto_approved_message[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if the request is auto-approved."""

    def wrapper(f: T) -> T:
        def wrapped(self: RequestType, identity: Identity, *args: Any, **kwargs: Any) -> Any:
            topic = kwargs["topic"]
            if is_auto_approved(self, identity=identity, topic=topic):
                return str(msg)
            return f(self, identity, *args, **kwargs)

        return cast("T", wrapped)

    return wrapper


def no_request_message[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if there is no request yet."""

    def wrapper(f: T) -> T:
        def wrapped(self: RequestType, identity: Identity, *args: Any, **kwargs: Any) -> Any:
            request = kwargs.get("request")
            if request:
                return str(msg)
            return f(self, identity, *args, **kwargs)

        return cast("T", wrapped)

    return wrapper


def request_message[T: Callable](condition: Callable[[Request, Identity], bool], msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if there is no request yet."""

    def wrapper(f: T) -> T:
        def wrapped(self: RequestType, identity: Identity, *args: Any, **kwargs: Any) -> Any:
            request = kwargs.get("request")
            if request and condition(request, identity):
                return str(msg)
            return f(self, identity, *args, **kwargs)

        return cast("T", wrapped)

    return wrapper


def on_request_submitted[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if the request is submitted."""

    def wrapper(f: T) -> T:
        return request_message(lambda r, _i: r.status == "submitted", msg)(f)

    return wrapper


def on_request_submitted_creator[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if the request is submitted by the creator."""

    def wrapper(f: T) -> T:
        return request_message(
            lambda r, i: r.status == "submitted" and request_identity_matches(r.created_by, i),
            msg,
        )(f)

    return wrapper


def on_request_submitted_receiver[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message to request receiver if the request is submitted."""

    def wrapper(f: T) -> T:
        return request_message(
            lambda r, i: r.status == "submitted" and request_identity_matches(r.receiver, i),
            msg,
        )(f)

    return wrapper


def on_request_creator[T: Callable](msg: LazyString) -> Callable[[T], T]:
    """Decorate a function to return a message if the request is has current identity as a creator."""

    def wrapper(f: T) -> T:
        return request_message(
            lambda r, i: request_identity_matches(r.created_by, i),
            msg,
        )(f)

    return wrapper


def add_record_to_community(
    record: Record,
    community: Community,
    request: Request | None,
    uow: UnitOfWork,
    default: bool = False,
) -> None:
    """Add record to community, ensuring the parent is also in the community."""
    record.parent.communities.add(community, request=request, default=default)

    service = current_runtime.get_record_service_for_record(record)

    uow.register(ParentRecordCommitOp(record.parent, indexer_context={"service": service}))
    uow.register(RecordIndexOp(record, indexer=service.indexer, index_refresh=True))


def change_primary_community(
    record: Record,
    community: Community,
    request: Request,
    uow: UnitOfWork,
) -> None:
    """Add record to community, ensuring the parent is also in the community."""
    record.parent.communities.remove(record.parent.communities.default)
    record.parent.communities.add(community, request=request, default=True)

    service = current_runtime.get_record_service_for_record(record)

    uow.register(ParentRecordCommitOp(record.parent, indexer_context={"service": service}))
    uow.register(RecordIndexOp(record, indexer=service.indexer, index_refresh=True))


def remove_record_from_community(
    record: Record,
    community: Community,
    uow: UnitOfWork,
) -> None:
    """Add record to community, ensuring the parent is also in the community."""
    record.parent.communities.remove(community)

    service = current_runtime.get_record_service_for_record(record)

    uow.register(ParentRecordCommitOp(record.parent, indexer_context={"service": service}))
    uow.register(RecordIndexOp(record, indexer=service.indexer, index_refresh=True))
