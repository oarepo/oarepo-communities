# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Proxy to access the extension instance."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from .ext import OARepoCommunities

current_oarepo_communities: OARepoCommunities = cast(
    "OARepoCommunities", LocalProxy(lambda: current_app.extensions["oarepo-communities"])
)
