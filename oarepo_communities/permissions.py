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

from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.record import CommunityRecordMixin

COMMUNITY_READ = 'community-read'
"""Action needed: read/list records in a community."""

COMMUNITY_CREATE = 'community-create'
"""Action needed: create a record in a community."""

COMMUNITY_REQUEST_APPROVAL = 'community-request-approval'
"""Action needed: request community record approval."""

COMMUNITY_APPROVE = 'community-approve'
"""Action needed: approve community record."""

COMMUNITY_REVERT_APPROVE = 'community-revert-approve'
"""Action needed: revert community record approval."""

COMMUNITY_REQUEST_CHANGES = 'community-request-changes'
"""Action needed: request changes to community record."""

COMMUNITY_PUBLISH = 'community-publish'
"""Action needed: publish community record."""

COMMUNITY_UNPUBLISH = 'community-unpublish'
"""Action needed: unpublish community record."""

ALLOWED_ACTIONS = [COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_REQUEST_APPROVAL, COMMUNITY_APPROVE,
                   COMMUNITY_REVERT_APPROVE, COMMUNITY_REQUEST_CHANGES, COMMUNITY_PUBLISH, COMMUNITY_UNPUBLISH]


def permission_factory(obj, action):
    """Get default permission factory.

    :param obj: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
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
