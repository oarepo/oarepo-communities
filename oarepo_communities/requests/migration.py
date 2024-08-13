import marshmallow as ma
from invenio_access.permissions import system_identity
from invenio_requests.proxies import current_requests_service
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.proxies import current_oarepo_requests_service
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityAlreadyIncludedException
from ..proxies import current_oarepo_communities


class InitiateCommunityMigrationAcceptAction(OARepoAcceptAction):
    """
    Source community accepting the initiate request autocreates confirm request delegated to the target community.
    """

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        creator_ref = ResolverRegistry.reference_identity(identity)
        request_item = current_oarepo_requests_service.create(
            system_identity,
            data={"payload": self.request["payload"]},
            request_type=ConfirmCommunityMigrationRequestType.type_id,
            topic=topic,
            creator=creator_ref,
            uow=uow,
            *args,
            **kwargs,
        )
        current_requests_service.execute_action(
            system_identity, request_item.id, "submit", uow=uow
        )


class ConfirmCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        community_id = self.request.receiver.resolve().community_id

        service = get_record_service_for_record(topic)
        community_inclusion_service = (
            current_oarepo_communities.community_inclusion_service
        )
        community_inclusion_service.remove(
            topic,
            str(topic.parent.communities.default.id),
            record_service=service,
            uow=uow,
        )
        community_inclusion_service.include(
            topic, community_id, record_service=service, uow=uow, default=True
        )


class InitiateCommunityMigrationRequestType(OARepoRequestType):
    """Request which is used to start migrating record from one primary community to another one.
    The recipient of this request type should be the community role of the current primary community, that is the owner
    of the current community must agree that the record could be migrated elsewhere.
    When this request is accepted, a new request of type ConfirmCommunityMigrationRequestType should be created and
     submitted to perform the community migration.
    """

    type_id = "initiate_community_migration"
    name = _("Inititiate Community migration")

    topic_can_be_none = False
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
    payload_schema = {
        "community": ma.fields.String(),
    }

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": InitiateCommunityMigrationAcceptAction,
        }

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        target_community_id = data["payload"]["community"]

        already_included = target_community_id == str(
            topic.parent.communities.default.id
        )
        if already_included:
            raise CommunityAlreadyIncludedException(
                "Already inside this primary community."
            )


class ConfirmCommunityMigrationRequestType(OARepoRequestType):
    """
    Performs the primary community migration. The recipient of this request type should be the community
    owner of the new community.
    """

    type_id = "confirm_community_migration"
    name = _("confirm Community migration")

    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": ConfirmCommunityMigrationAcceptAction,
        }
