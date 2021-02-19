# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

from __future__ import absolute_import, print_function

from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_communities = LocalProxy(
    lambda: current_app.extensions['oarepo-communities'])
"""Helper proxy to access oarepo-communities state object."""

current_permission_factory = LocalProxy(
    lambda: current_oarepo_communities.permission_factory)
"""Helper proxy to access to the configured permission factory."""
