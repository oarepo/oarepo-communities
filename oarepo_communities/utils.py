# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Version information for OARepo-Communities.

This file is imported by ``oarepo_communities.__init__``,
and parsed by ``setup.py``.
"""
from flask import request
from flask_babelex import gettext
from flask_login import current_user
from speaklater import make_lazy_gettext

from oarepo_communities.converters import CommunityPIDValue

_ = make_lazy_gettext(lambda: gettext)


def current_user_communities():
    """Returns a list of Community IDs the current user is member of."""
    roles = current_user.roles
    communities = []
    for role in roles:
        community = role.community.one_or_none()
        if community and community.id not in communities:
            communities.append(community.id)

    return communities


def community_id_from_request():
    """Returns community ID from request or None if ID could not be determined."""
    community_id = request.view_args.get('community_id')
    if not community_id:
        pid = request.view_args.get('pid_value')
        if pid and isinstance(pid.data[0].pid_value, CommunityPIDValue):
            community_id = pid.data[0].pid_value.community_id

    return community_id


def community_role_kwargs(community, role):
    """Returns role name for community-based roles."""
    return dict(
        name=f'community:{community.id}:{role}',
        description=f'{community.title} - {_(role)}',
    )


def community_kwargs_from_role(role):
    """Parses community id and role from role name."""
    args = role.name.split(':')
    if args[0] != 'community' or len(args) != 3:
        return None

    return dict(
        id_=args[1],
        role=args[2]
    )
