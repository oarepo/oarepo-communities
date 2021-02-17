# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from oarepo_communities.utils import community_role_kwargs

OAREPO_COMMUNITIES_ROLE_KWARGS = community_role_kwargs
"""Function returning an Invenio Role kwargs for a given community role."""

OAREPO_COMMUNITIES_ROLES = ['member', 'curator', 'publisher']
"""Roles present in each community."""
