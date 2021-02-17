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
from flask_babelex import gettext
from speaklater import make_lazy_gettext

_ = make_lazy_gettext(lambda: gettext)


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
