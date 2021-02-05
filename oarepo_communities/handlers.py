# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from oarepo_enrollment_permissions.handlers.collection import CollectionHandler


class CommunityHandler(CollectionHandler):
    """Handle enrollments, search & permission filtering in communities."""
