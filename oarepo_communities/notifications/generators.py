from invenio_access.models import User
from invenio_communities.members.records.models import MemberModel
from invenio_notifications.models import Recipient
from oarepo_requests.notifications.generators import SpecificEntityRecipient


class CommunityRoleEmailRecipient(SpecificEntityRecipient):
    """User recipient generator for a notification."""

    def __call__(self, notification, recipients):
        """Update required recipient information and add backend id."""
        community_role = self._resolve_entity()
        community_id = community_role.community_id
        role = community_role.role

        for user in (
            User.query.join(MemberModel)
            .filter(
                MemberModel.role == role, MemberModel.community_id == str(community_id)
            )
            .all()
        ):
            recipients[user.email] = Recipient(data={"email": user.email})
        return recipients
