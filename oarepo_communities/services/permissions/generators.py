from __future__ import annotations

import abc
import uuid
from collections import namedtuple
from functools import reduce
from typing import TYPE_CHECKING

from invenio_communities.communities.records.api import Community
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_communities.generators import CommunityRoleNeed, CommunityRoles
from invenio_communities.proxies import current_roles
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl
from oarepo_workflows.errors import MissingWorkflowError
from oarepo_workflows.requests import RecipientGeneratorMixin
from oarepo_workflows.services.permissions.generators import WorkflowPermission

from oarepo_communities.errors import (
    MissingCommunitiesError,
    MissingDefaultCommunityError,
    TargetCommunityNotProvidedException,
)
from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity, Need
    from invenio_drafts_resources.records import Record


def _user_in_community_need(user, community):
    _Need = namedtuple("Need", ["method", "value", "user", "community"])
    return _Need("user_in_community", f"{user}:{community}", user, community)


UserInCommunityNeed = _user_in_community_need


class InAnyCommunity(Generator):
    def __init__(self, permission_generator: Generator, **kwargs: Any) -> None:
        self.permission_generator = permission_generator
        super().__init__(**kwargs)

    def needs(self, **kwargs: Any) -> list[Need]:
        communities = CommunityMetadata.query.all()
        needs = set()  # to avoid duplicates
        # TODO: this is linear with number of communities, optimize
        # won't be easy to do as we go from community -> workflow id -> can_create/deposit
        # permission which might need a community id and currently can not process bulk
        # ids. Then we'd need a fallback to iteration if bulk fails.
        for community in communities:
            if community.slug is None:
                continue
            needs |= set(
                self.permission_generator.needs(
                    data={"parent": {"communities": {"default": str(community.id)}}},
                    community_metadata=community,  # optimization
                    **kwargs,
                )
            )
        return list(needs)


class CommunityWorkflowPermission(WorkflowPermission):

    def _get_workflow_id(self, record: Record = None, **kwargs: Any) -> str:
        # todo - check the record branch too? idk makes more sense to not use the default community's workflow, there is a deeper problem if there's no workflow on the record
        try:
            return super()._get_workflow_id(record=None, **kwargs)
        except MissingWorkflowError:
            if not record:
                workflow_id = current_oarepo_communities.get_community_default_workflow(
                    **kwargs
                )
                if not workflow_id:
                    raise MissingWorkflowError("Workflow not defined in input.")
                return workflow_id
            else:
                raise MissingWorkflowError("Workflow not defined on record.")


def convert_community_ids_to_uuid(community_id: str) -> str | uuid.UUID:
    # if it already is a string representation of uuid, keep it as it is
    try:
        uuid.UUID(community_id, version=4)  # ?
        return community_id
    except ValueError:
        community = Community.pid.resolve(community_id)
        return str(community.id)


class CommunityRoleMixin:
    def _get_record_communities(
        self, record: Record = None, **kwargs: Any
    ) -> list[str]:
        try:
            return record.parent.communities.ids
        except AttributeError:
            raise MissingCommunitiesError(f"Communities missing on record {record}.")

    def _get_data_communities(self, data: dict = None, **kwargs: Any) -> list[str]:
        community_ids = (data or {}).get("parent", {}).get("communities", {}).get("ids")
        if not community_ids:
            raise MissingCommunitiesError("Communities not defined in input data.")
        return [convert_community_ids_to_uuid(x) for x in community_ids]


class DefaultCommunityRoleMixin:
    def _get_record_communities(
        self, record: Record = None, **kwargs: Any
    ) -> list[str]:
        try:
            return [str(record.parent.communities.default.id)]
        except (AttributeError, TypeError) as e:
            try:
                return [str(record["parent"]["communities"]["default"])]
            except KeyError:
                raise MissingDefaultCommunityError(
                    f"Default community missing on record {record}."
                )

    def _get_data_communities(self, data: dict = None, **kwargs: Any) -> list[str]:
        community_id = (
            (data or {}).get("parent", {}).get("communities", {}).get("default")
        )
        if not community_id:
            raise MissingDefaultCommunityError(
                "Default community not defined in input data."
            )
        return [convert_community_ids_to_uuid(community_id)]


class OARepoCommunityRoles(CommunityRoles):
    # Invenio generators do not capture all situations where we need community id from record
    def communities(self, identity: Identity) -> list[str]:
        """Communities that an identity can manage."""
        roles = self.roles(identity=identity)
        community_ids = set()
        for n in identity.provides:
            if n.method == "community" and n.role in roles:
                community_ids.add(n.value)
        return list(community_ids)

    @abc.abstractmethod
    def _get_record_communities(
        self, record: Record = None, **kwargs: Any
    ) -> list[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_data_communities(self, data: dict = None, **kwargs: Any) -> list[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def roles(self, **kwargs: Any) -> list[str]:
        raise NotImplementedError()

    def needs(
        self, record: Record = None, data: dict = None, **kwargs: Any
    ) -> list[Need]:
        """Set of Needs granting permission."""
        _needs = set()

        if record and isinstance(record, Community):
            for role in self.roles(**kwargs):
                _needs.add(CommunityRoleNeed(str(record.id), role))
            return _needs

        if record:
            community_ids = self._get_record_communities(record)
        else:
            community_ids = self._get_data_communities(data)

        for c in community_ids:
            for role in self.roles(**kwargs):
                _needs.add(CommunityRoleNeed(c, role))
        return list(_needs)

    @abc.abstractmethod
    def query_filter_field(self) -> str:
        """Field for query filter.

        returns parent.communities.ids or parent.communities.default
        """
        raise NotImplementedError()

    def query_filter(self, identity: Identity = None, **kwargs: Any) -> dsl.Q:
        """Filter for current identity."""
        community_ids = self.communities(identity)
        if not community_ids:
            return dsl.Q("match_none")
        return dsl.Q("terms", **{self.query_filter_field(): community_ids})


class CommunityRole(CommunityRoleMixin, OARepoCommunityRoles):

    def __init__(self, role: str) -> None:
        self._role = role
        super().__init__()

    def roles(self, **kwargs: Any) -> list[str]:
        return [self._role]

    def query_filter_field(self) -> str:
        return "parent.communities.ids"


class DefaultCommunityRole(
    DefaultCommunityRoleMixin, RecipientGeneratorMixin, OARepoCommunityRoles
):

    def __init__(self, role: str) -> None:
        self._role = role
        super().__init__()

    def roles(self, **kwargs: Any) -> list[str]:
        return [self._role]

    def reference_receivers(self, **kwargs: Any) -> list[dict[str, str]]:
        community_id = self._get_record_communities(**kwargs)[0]
        return [{"community_role": f"{community_id}:{self._role}"}]

    def query_filter_field(self) -> str:
        return "parent.communities.default"


PrimaryCommunityRole = DefaultCommunityRole


class TargetCommunityRole(DefaultCommunityRole):

    def _get_data_communities(self, data: dict = None, **kwargs: Any) -> list[str]:
        try:
            community_id = data["payload"]["community"]
        except KeyError:
            raise TargetCommunityNotProvidedException(
                "Community not defined in request payload."
            )
        return [community_id]

    def reference_receivers(self, **kwargs: Any) -> list[dict[str, str]]:
        community_id = self._get_data_communities(**kwargs)[0]
        return [{"community_role": f"{community_id}:{self._role}"}]


class CommunityMembers(CommunityRoleMixin, OARepoCommunityRoles):

    def roles(self, **kwargs: Any) -> list[str]:
        """Roles."""
        return [r.name for r in current_roles]

    def query_filter_field(self) -> str:
        return "parent.communities.ids"


class DefaultCommunityMembers(DefaultCommunityRoleMixin, OARepoCommunityRoles):

    def roles(self, **kwargs: Any) -> list[str]:
        """Roles."""
        return [r.name for r in current_roles]

    def query_filter_field(self) -> str:
        return "parent.communities.default"


PrimaryCommunityMembers = DefaultCommunityMembers


class RecordOwnerInDefaultRecordCommunity(DefaultCommunityRoleMixin, Generator):
    default_or_ids = "default"

    def _record_communities(self, record: Record = None, **kwargs: Any) -> set[str]:
        return set(self._get_record_communities(record, **kwargs))

    def needs(
        self, record: Record = None, data: dict = None, **kwargs: Any
    ) -> list[Need]:
        record_communities = set(self._get_record_communities(record, **kwargs))
        return self._needs(record_communities, record=record)

    def _needs(self, record_communities: set[str], record: Record = None) -> list[Need]:
        owners = getattr(record.parent, "owners", None)
        ret = []
        for owner in owners:
            ret += [
                UserInCommunityNeed(owner.id, community)
                for community in record_communities
            ]
        return ret

    def query_filter(self, identity: Identity = None, **kwargs: Any) -> dsl.Q:
        """Filters for current identity as owner."""
        user_in_communities = {
            (n.user, n.community)
            for n in identity.provides
            if n.method == "user_in_community"
        }
        terms = []
        for element in user_in_communities:
            terms.append(
                dsl.Q("term", **{"parent.owners.user": element[0]})
                & dsl.Q(
                    "term", **{f"parent.communities.{self.default_or_ids}": element[1]}
                )
            )
        if not terms:
            return []
        query = reduce(lambda f1, f2: f1 | f2, terms)
        return query


RecordOwnerInPrimaryRecordCommunity = RecordOwnerInDefaultRecordCommunity


class RecordOwnerInRecordCommunity(
    CommunityRoleMixin, RecordOwnerInDefaultRecordCommunity
):
    default_or_ids = "ids"

    # trick to use CommunityRoleMixin instead of DefaultCommunityRoleMixin
    def _record_communities(self, record: Record = None, **kwargs: Any) -> set[str]:
        return set(self._get_record_communities(record, **kwargs))

    def needs(
        self, record: Record = None, data: dict = None, **kwargs: Any
    ) -> list[Need]:
        record_communities = set(self._get_record_communities(record, **kwargs))
        return self._needs(record_communities, record=record)
