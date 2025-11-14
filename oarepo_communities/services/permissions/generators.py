#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Permissions generators for communities service."""

from __future__ import annotations

import abc
import uuid
from functools import reduce, wraps
from typing import TYPE_CHECKING, NamedTuple, Protocol, cast, override

from flask_principal import Need
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_communities.generators import CommunityRoleNeed
from invenio_communities.proxies import current_roles
from invenio_db import db
from invenio_drafts_resources.records.api import Record as RecordWithParent
from invenio_search.engine import dsl
from oarepo_runtime.services.generators import Generator
from oarepo_workflows.errors import MissingWorkflowError
from oarepo_workflows.requests import RecipientGeneratorMixin
from oarepo_workflows.services.permissions import FromRecordWorkflow

from oarepo_communities.errors import (
    MissingCommunitiesError,
    MissingDefaultCommunityError,
    TargetCommunityNotProvidedError,
)
from oarepo_communities.proxies import current_oarepo_communities

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any

    from flask_principal import Identity
    from invenio_communities.generators import _Need as CommunityRoleNeedType
    from invenio_drafts_resources.records import Record
    from invenio_requests.customizations import RequestType
    from oarepo_workflows import Workflow


def require_draft_record(fn: Callable) -> Callable:
    """Ensure that the record is a draft."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "record" in kwargs and not isinstance(kwargs["record"], RecordWithParent):
            raise TypeError("Record in community must have a parent! Did you forget to use drafts?")
        return fn(*args, **kwargs)

    return wrapper


class UserInCommunityNeed(NamedTuple):
    """Need for user in community."""

    method: str
    value: str
    user: str | int
    community: str

    @classmethod
    def from_user_community(cls, user: str | int, community: str) -> UserInCommunityNeed:
        """Create need from user and community."""
        return cls("user_in_community", f"{user}:{community}", user, community)


class InAnyCommunity(Generator):
    """Generator that calls the internal permission generator for all communities."""

    def __init__(self, permission_generator: Generator, **kwargs: Any) -> None:
        """Create InAnyCommunity generator."""
        self.permission_generator = permission_generator
        super().__init__(**kwargs)

    @override
    def needs(self, **kwargs: Any) -> list[Need]:
        communities = db.session.query(CommunityMetadata).all()
        needs = set()  # to avoid duplicates
        # TODO: this is linear with number of communities, optimize
        # won't be easy to do as we go from community -> workflow id -> can_create/deposit
        # permission which might need a community id and currently can not process bulk
        # ids. Then we'd need a fallback to iteration if bulk fails.
        for community in communities:
            needs |= set(
                self.permission_generator.needs(
                    data={"parent": {"communities": {"default": str(community.id)}}},
                    community_metadata=community,  # optimization
                    **kwargs,
                )
            )
        return list(needs)


class CommunityWorkflowPermission(FromRecordWorkflow):
    """Permission generator wrapper that sets up workflow before calling the real generator.

    Permission generator that takes primarily the workflow from record's workflow.
    If it is not set, then it will look up the record's community and get the workflow
    id from the community's default workflow. If the record has no community, it will
    raise an exception.
    """

    @override
    @require_draft_record  # we are expecting a draft allowed framework to be always used with communities
    def _get_workflow(self, record: Record | None = None, **context: Any) -> Workflow:
        try:
            return super()._get_workflow(record=record, **context)
        except MissingWorkflowError as e:
            if not record:
                workflow_id = current_oarepo_communities.get_community_default_workflow(**context)
                if not workflow_id:
                    raise MissingWorkflowError("Workflow not defined in input.") from e
                return workflow_id
            raise


def convert_community_ids_to_uuid(community_id_or_slug: str) -> str:
    """Convert community id or slug to the string representation of uuid."""
    try:
        # try to parse it as uuid, if it works, return the canonical string representation
        return str(uuid.UUID(community_id_or_slug, version=4))
    except ValueError:
        # not a valid uuid, try to resolve as slug and return the stringified uuid
        community = Community.pid.resolve(community_id_or_slug)
        return str(community.id)


class CommunityRoleMixinProtocol(Protocol):
    """Mixin for community role generators. It provides methods to get communities from record or data."""

    def _get_record_communities(
        self,
        record: Record | None = None,
        **kwargs: Any,
    ) -> list[str]: ...

    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]: ...


class CommunityRoleMixin(CommunityRoleMixinProtocol):
    """Mixin for community role generators. It provides methods to get communities from record or data."""

    @override
    def _get_record_communities(
        self,
        record: Record | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Get community ids from record."""
        if not isinstance(record, RecordWithParent):
            raise TypeError("Record must contain a parent! Did you forget to use drafts?")
        try:
            return cast("list[str]", record.parent.communities.ids)
        except AttributeError as e:
            raise MissingCommunitiesError(f"Communities missing on record {record}.") from e

    @override
    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]:
        """Get community ids from input data."""
        community_ids = (data or {}).get("parent", {}).get("communities", {}).get("ids")
        if not community_ids:
            raise MissingCommunitiesError("Communities not defined in input data.")
        return [convert_community_ids_to_uuid(x) for x in community_ids]


class DefaultCommunityRoleMixin(CommunityRoleMixinProtocol):
    """Mixin for default community role generators.

    It provides methods to get only the default community from record or data.
    """

    @override
    def _get_record_communities(self, record: Record | None = None, **kwargs: Any) -> list[str]:
        if not isinstance(record, RecordWithParent):
            raise TypeError("Record must contain a parent! Did you forget to use drafts?")
        try:
            return [str(record.parent.communities.default.id)]
        except (AttributeError, TypeError):
            try:
                return [str(record["parent"]["communities"]["default"])]
            except KeyError as e:
                raise MissingDefaultCommunityError(f"Default community missing on record {record}.") from e

    @override
    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]:
        community_id = (data or {}).get("parent", {}).get("communities", {}).get("default", {})
        if not community_id:
            raise MissingDefaultCommunityError("Default community not defined in input data.")
        return [convert_community_ids_to_uuid(community_id)]


class OARepoCommunityRoles(CommunityRoleMixinProtocol, Generator, abc.ABC):
    """Base class for community role generators in OARepo.

    It is an extension of invenio's CommunityRoles generator. The community roles
    generator
    """

    def _get_identity_communities(self, identity: Identity) -> list[str]:
        """Return community ids that an identity has any rights in.

        Used in query filters to limit the search to communities the user has any rights in.
        """
        roles = self.roles(identity=identity)
        community_ids = set()
        for n in identity.provides:
            if n.method == "community" and cast("CommunityRoleNeedType", n).role in roles:
                community_ids.add(n.value)
        return list(community_ids)

    @abc.abstractmethod
    def roles(self, **kwargs: Any) -> list[str]:
        """Return list of roles that user must have (within record's communities) to get access."""
        raise NotImplementedError

    @override
    def needs(self, record: Record | None = None, data: dict | None = None, **kwargs: Any) -> list[Need]:
        """Set of Needs granting permission."""
        _needs = set[Need]()

        # if called on community, returns the required roles bound to the community id
        if record and isinstance(record, Community):
            for role in self.roles(**kwargs):
                _needs.add(CommunityRoleNeed(str(record.id), role))  # type: ignore[reportArgumentType]
            return list(_needs)

        community_ids = self._get_record_communities(record) if record is not None else self._get_data_communities(data)

        # create a need for each community and required roles. Will match if user
        # provides any of them
        for c in community_ids:
            for role in self.roles(**kwargs):
                # "invenio_communities.generators.Need" is not assignable to "flask_principal.Need"
                _needs.add(CommunityRoleNeed(c, role))  # type: ignore[reportArgumentType]
        return list(_needs)

    @abc.abstractmethod
    def query_filter_field(self) -> str:
        """Field for query filter.

        returns parent.communities.ids or parent.communities.default
        """
        raise NotImplementedError

    @override
    def query_filter(self, identity: Identity | None = None, **kwargs: Any) -> dsl.query.Query:
        """Filter for current identity."""
        if identity is None:
            return dsl.Q("match_none")  # type: ignore[no-any-return]

        community_ids = self._get_identity_communities(identity)
        if not community_ids:
            return dsl.Q("match_none")  # type: ignore[no-any-return]
        return dsl.Q("terms", **{self.query_filter_field(): community_ids})  # type: ignore[no-any-return]


class CommunityRole(CommunityRoleMixin, OARepoCommunityRoles):
    """Generator that allows access to records with primary or secondary communities within which user has role."""

    def __init__(self, role: str) -> None:
        """Create CommunityRole generator."""
        self._role = role
        super().__init__()

    @override
    def roles(self, **kwargs: Any) -> list[str]:
        """Return the required roles."""
        return [self._role]

    @override
    def query_filter_field(self) -> str:
        return "parent.communities.ids"


class DefaultCommunityRole(DefaultCommunityRoleMixin, RecipientGeneratorMixin, OARepoCommunityRoles):
    """Generator that allows access to records with default community within which user has role."""

    def __init__(self, role: str) -> None:
        """Create DefaultCommunityRole generator."""
        self._role = role
        super().__init__()

    @override
    def roles(self, **kwargs: Any) -> list[str]:
        return [self._role]

    @override
    @require_draft_record
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        community_id = self._get_record_communities(record=record, **context)[0]
        return [{"community_role": f"{community_id}:{self._role}"}]

    @override
    def query_filter_field(self) -> str:
        return "parent.communities.default"


PrimaryCommunityRole = DefaultCommunityRole


class TargetCommunityRole(DefaultCommunityRole):
    """A generator that checks the role for the community given in the request payload data.

    This is used, for example, in community join requests, where the target community
    is given in the request payload.
    """

    @override
    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]:
        if data is None:
            raise TargetCommunityNotProvidedError("Request data not provided.")
        try:
            community_id = data["payload"]["community"]
        except KeyError as e:
            raise TargetCommunityNotProvidedError("Community not defined in request payload.") from e
        return [community_id]

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        community_id = self._get_data_communities(record=record, **context)[0]
        return [{"community_role": f"{community_id}:{self._role}"}]


class CommunityMembers(CommunityRoleMixin, OARepoCommunityRoles):
    """Generator that allows access to records with primary or secondary communities within which user has any role."""

    @override
    def roles(self, **kwargs: Any) -> list[str]:
        """Roles."""
        return [r.name for r in current_roles]

    @override
    def query_filter_field(self) -> str:
        return "parent.communities.ids"


class DefaultCommunityMembers(DefaultCommunityRoleMixin, OARepoCommunityRoles):
    """Generator that allows access to records with default community within which user has any role."""

    @override
    def roles(self, **kwargs: Any) -> list[str]:
        """Roles."""
        return [r.name for r in current_roles]

    @override
    def query_filter_field(self) -> str:
        return "parent.communities.default"


PrimaryCommunityMembers = DefaultCommunityMembers


class RecordOwnerInRecordCommunityBase(CommunityRoleMixinProtocol, Generator):
    """Base class for generators that allow access to record owners only if they are members of the community."""

    default_or_ids: str

    @override
    @require_draft_record
    def needs(self, *, record: Record, data: dict | None = None, **kwargs: Any) -> list[Need]:
        record_communities = set(self._get_record_communities(record, **kwargs))
        return cast(
            "list[Need]", self._needs(record_communities, record=record)
        )  # there isn't a common ancestor for Need

    def _needs(self, record_communities: set[str], record: Record) -> list[UserInCommunityNeed]:
        needs: list[UserInCommunityNeed] = []
        owner_ids: list[int] = []

        if not isinstance(record, RecordWithParent):
            return []

        owners = getattr(record.parent.access, "owned_by", None)
        if owners is not None:
            owners = owners if isinstance(owners, list) else [owners]
            owner_ids = [owner.owner_id for owner in owners]

        for owner_id in owner_ids:
            needs += [UserInCommunityNeed.from_user_community(owner_id, community) for community in record_communities]
        return needs

    @override
    def query_filter(self, identity: Identity | None = None, **kwargs: Any) -> dsl.query.Query:
        """Create filters for current identity as owner."""
        if identity is None:
            return dsl.Q("match_none")  # type: ignore[no-any-return]

        user_in_communities = {
            (n.user, n.community)
            # not nice, but mypy can't infer the type otherwise and the if n.method guarantees
            # that it is of the right type
            for n in cast("list[UserInCommunityNeed]", identity.provides)
            if n.method == "user_in_community"
        }
        terms: list[Any] = [
            dsl.Q("term", **{"parent.owners.user": element[0]})
            & dsl.Q("term", **{f"parent.communities.{self.default_or_ids}": element[1]})
            for element in user_in_communities
        ]
        if not terms:
            return dsl.Q("match_none")  # type: ignore[no-any-return]

        return reduce(lambda f1, f2: f1 | f2, terms)  # type: ignore[no-any-return]


class RecordOwnerInDefaultRecordCommunity(DefaultCommunityRoleMixin, RecordOwnerInRecordCommunityBase):
    """Generator that allows access to owners of the record in its default community.

    The access is limited only when user is a member of the record's default community.
    When they stop being members, the access is removed.

    Note: this is different from invenio's RecordOwners generator, which allows access
    to all owners regardless of their community membership.

    Note: this generator needs that Identity.provides are loaded with UserInCommunityNeed.
    This is done by oarepo_communities.utils.load_community_user_needs
    """

    default_or_ids = "default"


RecordOwnerInPrimaryRecordCommunity = RecordOwnerInDefaultRecordCommunity


class RecordOwnerInRecordCommunity(CommunityRoleMixin, RecordOwnerInRecordCommunityBase):
    """Generator that allows access to owners of the record in any of its communities, primary or secondary."""

    default_or_ids = "ids"
