# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
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
