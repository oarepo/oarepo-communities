#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Proxy to access the extension instance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from .ext import OARepoCommunities

    current_oarepo_communities: OARepoCommunities

current_oarepo_communities = LocalProxy(  # type: ignore[assignment]
    lambda: current_app.extensions["oarepo-communities"]
)
