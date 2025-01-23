from oarepo_requests.notifications.generators import SpecificEntityRecipient
from invenio_access.permissions import system_identity
from invenio_notifications.models import Recipient
from invenio_search.engine import dsl
from invenio_communities.proxies import current_communities
from oarepo_requests.proxies import current_oarepo_requests

class CommunityRoleEmailRecipient(SpecificEntityRecipient):
    """User recipient generator for a notification."""

    def __call__(self, notification, recipients):
        """Update required recipient information and add backend id."""
        community_role = self._resolve_entity()
        community_id = community_role.community_id
        role = community_role.role

        filter_ = dsl.Q("term", **{"role": role})
        members = current_communities.service.members.scan(
            system_identity,
            community_id,
            extra_filter=filter_,
        )

        user_ids = []
        for m in members:
            if m["member"]["type"] != "user":
                continue
            user_ids.append(m["member"]["id"])

        if not user_ids:
            return recipients

        # todo - use link get_many in 'ui resolvers'
        entity_resolvers = current_oarepo_requests.entity_reference_ui_resolvers
        resolver = entity_resolvers["user"]
        users = resolver._search_many(system_identity, user_ids)
        mails = [u["email"] for u in users]
        for mail in mails:
            recipients[mail] = Recipient(data={"email": mail})