import marshmallow as ma
from invenio_access.permissions import system_identity
from invenio_records_resources.services.uow import RecordCommitOp
from invenio_requests.customizations.actions import RequestActions
from invenio_requests.errors import CannotExecuteActionError
from invenio_requests.proxies import current_requests_service
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_requests.actions.generic import OARepoAcceptAction
from oarepo_requests.proxies import current_oarepo_requests_service
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityAlreadyIncludedException
from ..utils import get_associated_service


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
        action_obj = RequestActions.get_action(request_item._record, "submit")
        if not action_obj.can_execute():
            raise CannotExecuteActionError("submit")
        action_obj.execute(identity, uow)
        uow.register(
            RecordCommitOp(
                request_item._record, indexer=current_requests_service.indexer
            )
        )


class ConfirmCommunityMigrationAcceptAction(OARepoAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        community_id = self.request.receiver.resolve().community_id

        service = get_record_service_for_record(topic)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.remove(
            topic, str(topic.parent.communities.default.id), uow=uow
        )
        record_communities_service.include(topic, community_id, uow=uow, default=True)


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

        # if it's included in the community as secondary?
        already_included = target_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException


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
