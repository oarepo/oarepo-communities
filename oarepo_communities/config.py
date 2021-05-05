# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_REQUEST_APPROVAL, \
    COMMUNITY_APPROVE, COMMUNITY_UNPUBLISH, COMMUNITY_PUBLISH, COMMUNITY_REQUEST_CHANGES, COMMUNITY_REVERT_APPROVE, \
    COMMUNITY_UPDATE, COMMUNITY_DELETE

OAREPO_COMMUNITIES_ROLES = ['member', 'curator', 'publisher']
"""Roles present in each community."""

OAREPO_COMMUNITIES_PERMISSION_FACTORY = 'oarepo_communities.permissions.permission_factory'
"""Permissions factory for Community record collections."""

OAREPO_COMMUNITIES_ROLE_NAME = 'oarepo_communities.utils.community_role_kwargs'
"""Factory that returns role name for community-based roles."""

OAREPO_COMMUNITIES_ROLE_PARSER = 'oarepo_communities.utils.community_kwargs_from_role'
"""Factory that parses community id and role from community role names."""

OAREPO_COMMUNITIES_ACTIONS_POLICY = 'oarepo_communities.utils.community_actions_policy'
"""Factory that takes a Community and returns role x actions policy matrix."""

OAREPO_COMMUNITIES_ALLOWED_ACTIONS = [COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_UPDATE,
                                      COMMUNITY_REQUEST_APPROVAL, COMMUNITY_APPROVE, COMMUNITY_REVERT_APPROVE,
                                      COMMUNITY_REQUEST_CHANGES, COMMUNITY_DELETE,
                                      COMMUNITY_PUBLISH, COMMUNITY_UNPUBLISH]
"""Community actions available to community roles."""

OAREPO_COMMUNITIES_ENDPOINTS = []
"""List of community enabled endpoints."""

OAREPO_COMMUNITIES_DEFAULT_ACTIONS = {
    'any': [],
    'author': [],
    'member': [COMMUNITY_CREATE],
    'curator': [COMMUNITY_READ, COMMUNITY_REQUEST_APPROVAL, COMMUNITY_APPROVE, COMMUNITY_UPDATE,
                COMMUNITY_REQUEST_CHANGES, COMMUNITY_DELETE],
    'publisher': [COMMUNITY_PUBLISH, COMMUNITY_REVERT_APPROVE]
}
"""Default action2role permission matrix for newly created communities."""
