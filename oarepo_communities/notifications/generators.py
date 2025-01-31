from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_access.models import User
from invenio_communities.members.records.models import MemberModel
from invenio_notifications.models import Recipient
from oarepo_requests.notifications.generators import SpecificEntityRecipient

if TYPE_CHECKING:
    from typing import Any


class CommunityRoleEmailRecipient(SpecificEntityRecipient):
    """Community role recipient generator for a notification."""

    def _get_recipients(self, entity: Any) -> dict[Recipient]:
        community_id = entity.community_id
        role = entity.role

        return {
            user.email: Recipient(data={"email": user.email})
            for user in (
                User.query.join(MemberModel)
                .filter(
                    MemberModel.role == role,
                    MemberModel.community_id == str(community_id),
                )
                .all()
            )
        }
