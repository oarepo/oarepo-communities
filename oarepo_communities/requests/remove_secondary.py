from __future__ import annotations

from typing import TYPE_CHECKING

from oarepo_requests.actions.generic import OARepoAcceptAction, RequestActionState
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityNotIncludedException, PrimaryCommunityException
from ..proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_records_resources.services.uow import UnitOfWork
    from invenio_requests.customizations import RequestType
    from invenio_requests.customizations.actions import RequestAction
    from oarepo_requests.typing import EntityReference


class RemoveSecondaryCommunityAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        community_id = self.request.receiver.resolve().community_id
        service = get_record_service_for_record(state.topic)
        community_inclusion_service = (
            current_oarepo_communities.community_inclusion_service
        )
        community_inclusion_service.remove(
            state.topic, community_id, record_service=service, uow=uow
        )


# Request
#
class RemoveSecondaryCommunityRequestType(OARepoRequestType):
    """Review request for submitting a record to a community."""

    type_id = "remove_secondary_community"
    name = _("Remove secondary community")

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    @classmethod
    @property
    def available_actions(cls) -> dict[str, type[RequestAction]]:
        return {
            **super().available_actions,
            "accept": RemoveSecondaryCommunityAcceptAction,
        }

    def can_create(
        self,
        identity: Identity,
        data: dict,
        receiver: EntityReference,
        topic: Record,
        creator: EntityReference,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data["payload"]["community"]
        not_included = target_community_id not in topic.parent.communities.ids
        if not_included:
            raise CommunityNotIncludedException(
                "Cannot remove, record is not in this community."
            )
        if target_community_id == str(topic.parent.communities.default.id):
            raise PrimaryCommunityException("Cannot remove record's primary community.")

    @classmethod
    def is_applicable_to(
        cls, identity: Identity, topic: Record, *args: Any, **kwargs: Any
    ) -> bool:
        super().is_applicable_to(identity, topic, *args, **kwargs)
        try:
            communities = topic.parent.communities.ids
        except AttributeError:
            return False
        if len(communities) < 2:
            return False
        return super().is_applicable_to(identity, topic, *args, **kwargs)
