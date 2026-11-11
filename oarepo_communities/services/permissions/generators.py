# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Permissions generators for communities service."""

from __future__ import annotations

import abc
import copy
import uuid
from functools import wraps
from typing import TYPE_CHECKING, Protocol, cast, override

from flask import current_app
from flask_principal import Need
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_communities.generators import CommunityRoleNeed
from invenio_communities.proxies import current_roles
from invenio_db import db
from invenio_drafts_resources.records.api import Record as RecordWithParent
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl
from oarepo_runtime.typing import require_kwargs
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import RecipientGeneratorMixin
from oarepo_workflows.services.permissions.composite import RequireAll

from oarepo_communities.utils import (
    get_community_ids_from_record,
    get_default_community_id_from_record,
)
from oarepo_communities.workflow import get_allowed_workflows

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any

    from flask_principal import Identity
    from invenio_communities.generators import _Need as CommunityRoleNeedType
    from invenio_drafts_resources.records import Record
    from invenio_requests.customizations import RequestType


def require_draft_record(fn: Callable) -> Callable:
    """Ensure that the record is a draft."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "record" in kwargs and not isinstance(kwargs["record"], RecordWithParent):
            raise TypeError("Record in community must have a parent! Did you forget to use drafts?")
        return fn(*args, **kwargs)

    return wrapper


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

        # the data might have been passed, for example during can_create = [InAnyCommunity(...)]
        # if so, we need to shallow copy the data to avoid modifying the original
        data = kwargs.pop("data", None)
        data = {**data} if data is not None else {}

        # and if parent is present, we deepcopy it as we will change the communities dict inside
        if "parent" in data:
            data["parent"] = copy.deepcopy(data["parent"])
        else:
            data["parent"] = {}

        for community in communities:
            data["parent"]["communities"] = {"default": str(community.id)}
            needs |= set(
                self.permission_generator.needs(
                    data=data,
                    community_metadata=community,  # optimization
                    **kwargs,
                )
            )
        return list(needs)


class CanSubmitRecordInCommunity(Generator):
    """Generator that checks if the user can submit a record in a community."""

    # serialized dict comes for ui
    @override
    @require_kwargs("record")
    def needs(self, record: Community | dict[str, Any], **kwargs: Any) -> list[Need]:
        ret: set[Need] = set()
        custom_fields_dict: dict[str, str | list[str]] = (
            record.custom_fields if isinstance(record, Community) else record.get("custom_fields", {})
        ) or {}
        wfs: list[str] = get_allowed_workflows(custom_fields_dict)
        for workflow_code in wfs:
            workflow = current_oarepo_workflows.workflow_by_code[workflow_code]
            requests = workflow.requests().requests_by_id
            if "community-submission" not in requests:
                current_app.logger.error("Workflow %s does not have community-submission request", workflow_code)
                continue
            ret |= set(
                requests["community-submission"].requester_generator.needs(record=record, community=record, **kwargs)
            )
        return list(ret)


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
            return get_community_ids_from_record(record)
        except AttributeError:
            return []

    @override
    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]:
        """Get community ids from input data."""
        community_ids = (data or {}).get("parent", {}).get("communities", {}).get("ids")
        if not community_ids:
            return []
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
            return [get_default_community_id_from_record(record)]
        except AttributeError, TypeError:
            return []

    @override
    def _get_data_communities(self, data: dict | None = None, **kwargs: Any) -> list[str]:
        community_id = (data or {}).get("parent", {}).get("communities", {}).get("default", None)
        if not community_id:
            return []
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
                _needs.add(CommunityRoleNeed(str(record.id), role))
            return list(_needs)

        community_ids = []
        try:
            community_ids = self._get_record_communities(record) if record else self._get_data_communities(data)
        except TypeError:
            # the record does not have a parent, if there is community passed in kwargs, use it,
            # otherwise raise the original error
            if not (kwargs.get("community")):
                raise

        # (back up to permission policy class) that passes the community into **over at instanciating
        # the policy class
        if not community_ids and "community" in kwargs and kwargs["community"]:
            community = kwargs["community"]
            community_ids = [str(community.id)] if isinstance(community, Community) else [str(community["id"])]

        # create a need for each community and required roles. Will match if user
        # provides any of them
        for c in community_ids:
            for role in self.roles(**kwargs):
                # "invenio_communities.generators.Need" is not assignable to "flask_principal.Need"
                _needs.add(CommunityRoleNeed(c, role))
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
            return dsl.Q("match_none")

        community_ids = self._get_identity_communities(identity)
        if not community_ids:
            return dsl.Q("match_none")
        return dsl.Q("terms", **{self.query_filter_field(): community_ids})


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
        community_ids = self._get_record_communities(record=record, **context)
        return [{"community_role": f"{community_ids[0]}:{self._role}"}] if community_ids else []

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
            return []
        try:
            community_id = data["payload"]["community"]
        except KeyError:
            return []
        return [community_id]

    @override
    @require_draft_record
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        community_ids = self._get_data_communities(record=record, **context)
        return [{"community_role": f"{community_ids[0]}:{self._role}"}] if community_ids else []


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


class RecordOwnerInRecordCommunity(RequireAll):
    """Allows record owners only while they are members of any of the record's communities.

    Unlike invenio's RecordOwners, the access is lost when the owner leaves the communities.
    The hosting permission policy must inherit from BooleanPermissionPolicyMixin.
    """

    def __init__(self) -> None:
        """Create the generator."""
        super().__init__(RecordOwners(), CommunityMembers())


class RecordOwnerInDefaultRecordCommunity(RequireAll):
    """Allows record owners only while they are members of the record's default community.

    The hosting permission policy must inherit from BooleanPermissionPolicyMixin.
    """

    def __init__(self) -> None:
        """Create the generator."""
        super().__init__(RecordOwners(), DefaultCommunityMembers())


RecordOwnerInPrimaryRecordCommunity = RecordOwnerInDefaultRecordCommunity
