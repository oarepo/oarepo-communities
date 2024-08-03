import marshmallow as ma
from oarepo_requests.types import ModelRefTypes
from oarepo_requests.types.generic import OARepoRequestType
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from oarepo_runtime.i18n import lazy_gettext as _

from ..errors import CommunityAlreadyIncludedException
from ..resolvers.communities import CommunityRoleObj
from ..utils import get_associated_service
from .submission import (
    AbstractCommunitySubmissionRequestType,
    CommunitySubmissionAcceptAction,
)

# todo: accept action for for initiate request
class ConfirmCommunityMigrationAcceptAction(CommunitySubmissionAcceptAction):
    """Accept action."""
    def apply(self, identity, request_type, topic, uow, *args, **kwargs):
        # coordination along multiple submission like requests? can only one be available at time?
        # ie.
        # and what if the community is deleted before the request is processed?
        service = get_record_service_for_record(topic)
        record_communities_service = get_associated_service(
            service, "record_communities"
        )
        record_communities_service.remove(
            topic, str(topic.parent.communities.default.id), uow=uow
        )
        super().apply(identity, request_type, topic, uow, *args, **kwargs)


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
    available_actions = {
        **AbstractCommunitySubmissionRequestType.available_actions,
        "accept": ConfirmCommunityMigrationAcceptAction,
    }
