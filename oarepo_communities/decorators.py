# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from functools import wraps

from invenio_files_rest.views import check_permission

from oarepo_communities.proxies import current_permission_factory


def need_permissions(object_getter, action, hidden=True):
    """Get permission on Community Record action or abort.

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
