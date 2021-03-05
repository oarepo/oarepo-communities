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
from flask_principal import UserNeed
from invenio_access import action_factory, SystemRoleNeed, Permission, ParameterizedActionNeed
from invenio_records import Record
from invenio_records_rest.utils import deny_all, allow_all
from oarepo_fsm.permissions import require_any, require_all

from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_DELETE, PRIMARY_COMMUNITY_FIELD
from oarepo_communities.proxies import current_oarepo_communities


community_record_owner = SystemRoleNeed('community-record-owner')


def action_permission_factory(action):
    """Community action permission factory.

    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """

    def inner(record, *args, **kwargs):
        if action not in current_oarepo_communities.allowed_actions:
            return deny_all()

        if record is None:
            raise RuntimeError('Record is missing.')

        arg = None
        if isinstance(record, Record):
            arg = record.primary_community
        elif isinstance(record, dict):
            arg = record[PRIMARY_COMMUNITY_FIELD]
        else:
            raise RuntimeError('Unknown or missing object')
        return Permission(ParameterizedActionNeed(action, arg))

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
        return Permission(*[action_factory(COMMUNITY_READ, parameter=True)(x) for x in communities])
    else:
        raise RuntimeError('Unknown or missing object')


def owner_permission_factory(action):
    """Owner permission factory.

    Permission factory that requires user to be both the owner of the
    accessed record and that required action is granted to record owners.
    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    return require_all(
        owner_permission_impl,
        action_permission_factory(f'owner-{action}')
    )


def owner_permission_impl(record, *args, **kwargs):
    owners = record['access']['owned_by']
    return Permission(
        *[UserNeed(int(owner)) for owner in owners],
    )


def owner_or_role_action_permission_factory(action):
    return require_any(
        action_permission_factory(action),
        owner_permission_factory(action)
    )


def create_permission_factory(record, *args, **kwargs):
    """Records REST create permission factory."""
    return Permission(ParameterizedActionNeed(COMMUNITY_CREATE, request.view_args['community_id']))


def update_permission_factory(record, *args, **kwargs):
    """Records REST update permission factory."""
    # TODO: tady by mel byt autor recordu
    return allow_all


def delete_permission_factory(record, *args, **kwargs):
    """Records REST delete permission factory."""
    return action_permission_factory(COMMUNITY_DELETE)


read_object_permission_impl = require_any(
    read_permission_factory
)

create_object_permission_impl = require_any(
    create_permission_factory
)

update_object_permission_impl = require_any(
    update_permission_factory
)

delete_object_permission_impl = require_any(
    delete_permission_factory
)
