import abc

from invenio_communities.generators import (
    CommunityCurators,
    CommunityMembers,
    CommunityRoleNeed, CommunityRoles,
)
from invenio_communities.proxies import current_roles
from invenio_rdm_records.services.generators import RecordCommunitiesAction
from invenio_records_permissions.generators import Generator
from oarepo_workflows.requests.policy import RecipientGeneratorMixin

from oarepo_communities.errors import MissingDefaultCommunityError, MissingCommunitiesError
from oarepo_communities.proxies import current_oarepo_communities

class CommunityRoleMixin:
    def _get_record_communities(self, record=None, **kwargs):
        try:
            return record.parent.communities.ids
        except AttributeError:
            raise MissingCommunitiesError(f"Communities missing on record {record}.")

    def _get_data_communities(self, data=None, **kwargs):
        community_ids = (
            (data or {})
            .get("parent", {})
            .get("communities", {})
            .get("ids")
        )
        if not community_ids:
            raise MissingCommunitiesError("Communities not defined in input data.")
        return community_ids

class DefaultCommunityRoleMixin:
    def _get_record_communities(self, record=None, **kwargs):
        try:
            return [str(record.parent.communities.default.id)]
        except AttributeError:
            raise MissingDefaultCommunityError(f"Default community missing on record {record}.")

    def _get_data_communities(self, data=None, **kwargs):
        community_id = (
            (data or {})
            .get("parent", {})
            .get("communities", {})
            .get("default")
        )
        if not community_id:
            raise MissingDefaultCommunityError("Default community not defined in input data.")
        return [community_id]

class OARepoCommunityRoles(CommunityRoles):
    # Invenio generators do not capture all situations where we need community id from record
    def communities(self, identity):
        """Communities that an identity can manage."""
        roles = self.roles(identity=identity)
        community_ids = set()
        for n in identity.provides:
            if n.method == "community" and n.role in roles:
                community_ids.add(n.value)
        return list(community_ids)
    @abc.abstractmethod
    def _get_record_communities(self, record=None, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def _get_data_communities(self, data=None, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def roles(self, **kwargs):
        raise NotImplemented()

    def needs(self, record=None, data=None, **kwargs):
        """Set of Needs granting permission."""
        if record:
            community_ids = self._get_record_communities(record)
        else:
            community_ids = self._get_data_communities(data)

        _needs = set()
        for c in community_ids:
            for role in self.roles(**kwargs):
                _needs.add(CommunityRoleNeed(c, role))
        return _needs


class CommunityRole(CommunityRoleMixin, OARepoCommunityRoles):

    def __init__(self, role):
        self._role = role
        super().__init__()
    def roles(self, **kwargs):
        return [self._role]



class DefaultCommunityRole(DefaultCommunityRoleMixin, RecipientGeneratorMixin, OARepoCommunityRoles):

    def __init__(self, role):
        self._role = role
        super().__init__()
    def roles(self, **kwargs):
        return [self._role]

    def reference_receivers(self, **kwargs):
        community_id = self._get_record_communities(**kwargs)[0]
        return [{"community_role": f"{community_id} : {self._role}"}]


class TargetCommunityRole(CommunityRole):

    def _get_data_communities(self, data=None, **kwargs):
        try:
            community_id = data["payload"]["community"]
        except KeyError:
            raise MissingDefaultCommunityError("Community not defined in request payload.")
        return [community_id]

    def reference_receivers(self, **kwargs):
        community_id = self._get_data_communities(**kwargs)[0]
        return [{"community_role": f"{community_id} : {self._role}"}]



class CommunityMembers(CommunityRoleMixin, OARepoCommunityRoles):

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles]

class DefaultCommunityMembers(DefaultCommunityRoleMixin, OARepoCommunityRoles):

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles]


    """"""
