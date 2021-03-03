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
from flask_principal import Permission, ActionNeed
from invenio_records_rest.utils import deny_all

from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.record import CommunityRecordMixin


def permission_factory(obj, action):
    """Get default permission factory.

    :param obj: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    if action not in current_oarepo_communities.allowed_actions:
        return deny_all()

    arg = None
    if isinstance(obj, CommunityRecordMixin):
        arg = obj.primary_community
    elif isinstance(obj, OARepoCommunityModel):
        arg = obj.id
    elif isinstance(obj, dict):
        arg = obj[CommunityRecordMixin.PRIMARY_COMMUNITY_FIELD]
    else:
        raise RuntimeError('Unknown or missing object')

    return Permission(ActionNeed(action, arg))
