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
from flask_principal import UserNeed
from invenio_access import action_factory, SystemRoleNeed, Permission
from invenio_records import Record
from invenio_records_rest.utils import deny_all, allow_all
from oarepo_fsm.permissions import require_any, require_all

from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_DELETE, PRIMARY_COMMUNITY_FIELD
from oarepo_communities.proxies import current_oarepo_communities


def permission_factory(action):
    """Get default permission factory.

    :param obj: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """

    def inner(obj=None):
        if action not in current_oarepo_communities.allowed_actions:
            return deny_all()

        arg = None
        if isinstance(obj, Record):
            arg = obj.primary_community
        elif isinstance(obj, dict):
            arg = obj[PRIMARY_COMMUNITY_FIELD]
        else:
            raise RuntimeError('Unknown or missing object')
        return Permission(action_factory(action, parameter=True)(arg))

    return inner


def owner_permission_impl(record, *args, **kwargs):
    owners = record['access']['owned_by']
    return Permission(
        *[UserNeed(int(owner)) for owner in owners],
    )


def owner_permission_factory(action):
    return require_all(
        owner_permission_impl,
        permission_factory(f'owner-{action}')
    )


def read_permission_factory(record):
    """Get default permission factory.

    :param obj: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    if isinstance(record, Record):
        communities = [record.primary_community, *record.secondary_communities]
        return Permission(*[action_factory(COMMUNITY_READ, parameter=True)(x) for x in communities])
    else:
        raise RuntimeError('Unknown or missing object')


community_record_owner = SystemRoleNeed('community-record-owner')


def create_permission_factory(community):
    """Records REST create permission factory."""
    return permission_factory(COMMUNITY_CREATE)


def update_permission_factory(record):
    """Records REST update permission factory."""
    # TODO: tady by mel byt autor recordu
    return allow_all


def delete_permission_factory(record):
    """Records REST delete permission factory."""
    return permission_factory(COMMUNITY_DELETE)


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
