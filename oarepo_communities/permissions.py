# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

#
# Action needs
#
from flask import request
from flask_principal import UserNeed, RoleNeed
from invenio_access import SystemRoleNeed, Permission, ParameterizedActionNeed
from invenio_records import Record
from oarepo_fsm.permissions import require_any, require_all, state_required

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_DELETE, \
    STATE_EDITING, STATE_PENDING_APPROVAL, COMMUNITY_REQUEST_CHANGES, COMMUNITY_APPROVE, \
    STATE_APPROVED, COMMUNITY_REVERT_APPROVE, COMMUNITY_PUBLISH, STATE_PUBLISHED, \
    COMMUNITY_UNPUBLISH, COMMUNITY_UPDATE, \
    COMMUNITY_REQUEST_APPROVAL
from oarepo_communities.proxies import current_oarepo_communities

community_record_owner = SystemRoleNeed('community-record-owner')


def require_action_allowed(action):
    """
    Permission factory that requires the action to be allowed by configuration.

    You can use
    ```
        require_all(require_action_allowed(COMMUNITY_CREATE), Permission(RoleNeed('editor')))
    ```
    """

    def factory(record=None, *_args, **_kwargs):
        def can():
            return action in current_oarepo_communities.allowed_actions

        return type('ActionAllowedPermission', (), {'can': can})

    return factory


def action_permission_factory(action):
    """Community action permission factory.

    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """

    def inner(record, *args, **kwargs):
        if record is None:
            raise RuntimeError('Record is missing.')

        arg = None
        if isinstance(record, Record):
            arg = record.primary_community
        elif isinstance(record, dict):
            arg = current_oarepo_communities.get_primary_community_field(record)
        else:
            raise RuntimeError('Unknown or missing object')
        return require_all(
            require_action_allowed(action),
            Permission(ParameterizedActionNeed(action, arg)))

    return inner


def read_permission_factory(record, *args, **kwargs):
    """Read permission factory that takes secondary communities into account.

    :param record: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    if isinstance(record, Record):
        communities = [record.primary_community, *record.secondary_communities]
        return require_all(
            require_action_allowed(COMMUNITY_READ),
            Permission(*[ParameterizedActionNeed(COMMUNITY_READ, x) for x in communities])
        )(record, *args, **kwargs)
    else:
        raise RuntimeError('Unknown or missing object')


def owner_permission_factory(action, record, *args, **kwargs):
    """Owner permission factory.

    Permission factory that requires user to be both the owner of the
    accessed record and that required action is granted to record owners.
    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    return require_all(
        owner_permission_impl,
        action_permission_factory(f'owner-{action}')(record, *args, **kwargs)
    )


def community_role_permission_factory(role):
    """Community role permission factory.
       :param role: Community role name.
    """

    def inner(record, *args, **kwargs):
        community = OARepoCommunity.get_community(request.view_args['community_id'])
        return Permission(RoleNeed(OARepoCommunity.get_role(community, role).name))

    return inner


def community_member_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('member')(record, *args, **kwargs)


def community_curator_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('curator')(record, *args, **kwargs)


def community_publisher_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('publisher')(record, *args, **kwargs)


def owner_permission_impl(record, *args, **kwargs):
    owners = current_oarepo_communities.get_owned_by_field(record)
    return Permission(
        *[UserNeed(int(owner)) for owner in owners],
    )


def owner_or_role_action_permission_factory(action, record, *args, **kwargs):
    return require_any(
        action_permission_factory(action)(record, *args, **kwargs),
        owner_permission_factory(action, record, *args, **kwargs)
    )(record, *args, **kwargs)


def create_permission_factory(record, community_id=None, *args, **kwargs):
    """Records REST create permission factory."""
    # return action_permission_factory(COMMUNITY_CREATE)
    return Permission(ParameterizedActionNeed(COMMUNITY_CREATE,
                                              community_id or request.view_args['community_id']))


def update_permission_factory(record, *args, **kwargs):
    """Records REST update permission factory."""
    return require_all(
        state_required(STATE_EDITING, STATE_PENDING_APPROVAL),
        action_permission_factory(COMMUNITY_UPDATE)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def delete_permission_factory(record, *args, **kwargs):
    """Records REST delete permission factory."""
    return owner_or_role_action_permission_factory(COMMUNITY_DELETE, record, *args, **kwargs)


def request_approval_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(None, STATE_EDITING),
        owner_or_role_action_permission_factory(COMMUNITY_REQUEST_APPROVAL, record)
    )(record, *args, **kwargs)


def delete_draft_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(None, STATE_EDITING, STATE_PENDING_APPROVAL),
        owner_or_role_action_permission_factory(COMMUNITY_DELETE, record)
    )(record, *args, **kwargs)


def request_changes_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(STATE_PENDING_APPROVAL),
        action_permission_factory(COMMUNITY_REQUEST_CHANGES)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def approve_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(STATE_PENDING_APPROVAL),
        action_permission_factory(COMMUNITY_APPROVE)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def revert_approval_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(STATE_APPROVED),
        action_permission_factory(COMMUNITY_REVERT_APPROVE)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def publish_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(STATE_APPROVED),
        action_permission_factory(COMMUNITY_PUBLISH)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def unpublish_permission_factory(record, *args, **kwargs):
    return require_all(
        state_required(STATE_PUBLISHED),
        action_permission_factory(COMMUNITY_UNPUBLISH)(record, *args, **kwargs)
    )(record, *args, **kwargs)


# REST endpoints permission factories.
read_object_permission_impl = require_any(
    # Anyone can read published records
    state_required(STATE_PUBLISHED),
    # Roles with granted READ action in record's primary or secondary communities can read
    read_permission_factory
)

create_object_permission_impl = create_permission_factory

update_object_permission_impl = update_permission_factory

delete_object_permission_impl = delete_permission_factory

# Record actions permission factories.
request_approval_permission_impl = request_approval_permission_factory

delete_draft_permission_impl = delete_draft_permission_factory

request_changes_permission_impl = request_changes_permission_factory

approve_permission_impl = approve_permission_factory

revert_approval_permission_impl = revert_approval_permission_factory

publish_permission_impl = publish_permission_factory

unpublish_permission_impl = unpublish_permission_factory
