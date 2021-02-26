# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from functools import wraps

#
# Action needs
#
from flask_principal import Permission
from invenio_access import action_factory
from invenio_files_rest.views import check_permission

from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.proxies import current_permission_factory
from oarepo_communities.record import CommunityRecordMixin

RequestApproval = action_factory('community-request-approval', parameter=True)
"""Action needed: request community record approval."""

Approve = action_factory('community-approve', parameter=True)
"""Action needed: approve community record."""

RevertApprove = action_factory('community-revert-approve', parameter=True)
"""Action needed: revert community record approval."""

RequestChanges = action_factory('community-request-changes', parameter=True)
"""Action needed: request changes to community record."""

Publish = action_factory('community-publish', parameter=True)
"""Action needed: publish community record."""

Unpublish = action_factory('community-unpublish', parameter=True)
"""Action needed: unpublish community record."""

_action2need_map = {
    'request-approval': RequestApproval,
    'approve': Approve,
    'revert-approve': RevertApprove,
    'request-changes': RequestChanges,
    'publish': Publish,
    'unpublish': Unpublish
}
"""Mapping of action names to action needs."""


def permission_factory(obj, action):
    """Get default permission factory.

    :param obj: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    need_class = _action2need_map[action]
    arg = None
    if isinstance(obj, CommunityRecordMixin):
        arg = obj.primary_community
    elif isinstance(obj, OARepoCommunityModel):
        arg = obj.id
    else:
        raise RuntimeError('Unknown or missing object')

    return Permission(need_class(arg))


def need_permissions(object_getter, action, hidden=True):
    """Get permission for Community Record abort.

    :param object_getter: The function used to retrieve the object and pass it
        to the permission factory.
    :param action: The action needed.
    :param hidden: Determine which kind of error to return. (Default: ``True``)
    """
    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            check_permission(current_permission_factory(
                object_getter(*args, **kwargs),
                action(*args, **kwargs) if callable(action) else action,

            ), hidden=hidden)
            return f(*args, **kwargs)
        return decorate
    return decorator_builder
