#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Request type for removing a record from a secondary community."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import marshmallow as ma
from invenio_drafts_resources.records import Record as RecordWithParent
from invenio_i18n import lazy_gettext as _
from invenio_notifications.services.uow import NotificationOp
from invenio_rdm_records.notifications.builders import (
    CommunityInclusionAcceptNotificationBuilder,
)
from invenio_requests.customizations.actions import RequestAction
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.types.generic import NonDuplicableOARepoRecordRequestType
from oarepo_requests.utils import classproperty

from ..errors import CommunityNotIncludedError, PrimaryCommunityError
from .utils import remove_record_from_community

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_records_resources.records import Record


class RemoveSecondaryCommunityAcceptAction(OARepoAcceptAction):
    """Accept action."""

    @override
    def apply(
        self,
        identity: Identity,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        community = self.request["payload"]["community"]

        remove_record_from_community(cast("RecordWithParent", self.topic), community, uow)

        if kwargs.get("send_notification", True):
            uow.register(
                NotificationOp(
                    CommunityInclusionAcceptNotificationBuilder.build(identity=identity, request=self.request)
                )
            )


# Request
#
class RemoveSecondaryCommunityRequestType(NonDuplicableOARepoRecordRequestType):
    """Review request for submitting a record to a community."""

    type_id = "remove_secondary_community"
    name = _("Remove secondary community")

    payload_schema: Mapping[str, ma.fields.Field] | None = {
        "community": ma.fields.Str(required=True),
    }

    creator_can_be_none = False
    topic_can_be_none = False

    @classproperty[dict[str, type[RequestAction]]]
    @override
    def available_actions(  # type: ignore[override] # TODO: fix in requests
        cls,  # noqa: N805
    ) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": RemoveSecondaryCommunityAcceptAction,
        }

    @override
    def can_create(
        self,
        identity: Identity,
        data: dict,
        receiver: dict[str, str],
        topic: Record,
        creator: dict[str, str],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data["payload"]["community"]
        if not isinstance(topic, RecordWithParent):
            raise CommunityNotIncludedError("Record has no parent.")

        not_included = target_community_id not in topic.parent.communities.ids
        if not_included:
            raise CommunityNotIncludedError("Cannot remove, record is not in this community.")
        if target_community_id == str(topic.parent.communities.default.id):
            raise PrimaryCommunityError("Cannot remove record's primary community.")

    @classmethod
    @override
    def is_applicable_to(cls, identity: Identity, topic: Record, *args: Any, **kwargs: Any) -> bool:
        super().is_applicable_to(identity, topic, *args, **kwargs)
        if not isinstance(topic, RecordWithParent):
            return False
        try:
            communities = topic.parent.communities.ids
        except AttributeError:
            return False
        if len(communities) > 1:
            return cast("bool", super().is_applicable_to(identity, topic, *args, **kwargs))
        return False
