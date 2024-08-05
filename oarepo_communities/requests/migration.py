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
from oarepo_workflows.proxies import current_oarepo_workflows

from ..errors import CommunityAlreadyIncludedException
from ..proxies import current_oarepo_communities
from ..resolvers.communities import CommunityRoleObj
from ..utils import get_associated_service, resolve_community
from .submission import (
    AbstractCommunitySubmissionRequestType,
    CommunitySubmissionAcceptAction,
)


class InitiateCommunityMigrationAcceptAction(OARepoAcceptAction):
    """
    Source community accepting the initiate request autocreates confirm request delegated to the target community.
    """

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        request = self.request
        creator_ref = ResolverRegistry.reference_identity(identity)
        request_item = current_oarepo_requests_service.create(
            system_identity,
            data={"payload": request["payload"]},
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


class ConfirmCommunityMigrationAcceptAction(CommunitySubmissionAcceptAction):
    """Accept action."""

    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        community = self.request.receiver.resolve()
        community = resolve_community(community)

        service = get_record_service_for_record(topic)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.remove(
            topic, str(topic.parent.communities.default.id), uow=uow
        )
        super().apply(
            identity, request_type, topic, uow, *args, community=community, **kwargs
        )
        new_default_workflow = (
            current_oarepo_communities.get_community_default_workflow(
                community_id=community.id
            )
        )
        current_oarepo_workflows.set_workflow(
            identity, topic, new_default_workflow, uow=uow, **kwargs
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
        receiver_community_id = (
            CommunityRoleObj.community_role_or_community_ref_get_community_id(
                data["payload"]["community"]
            )
        )
        # if it's included in the community as secondary?
        already_included = receiver_community_id in topic.parent.communities.ids
        if already_included:
            raise CommunityAlreadyIncludedException


class ConfirmCommunityMigrationRequestType(AbstractCommunitySubmissionRequestType):
    """
    Performs the primary community migration. The recipient of this request type should be the community
    owner of the new community.
    """

    type_id = "confirm_community_migration"
    name = _("confirm Community migration")
    set_as_default = True

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": ConfirmCommunityMigrationAcceptAction,
        }
