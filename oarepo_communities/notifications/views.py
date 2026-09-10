#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Notification template blueprint."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint

if TYPE_CHECKING:
    from flask import Flask


def create_blueprint(_app: Flask) -> Blueprint:
    """Expose the package's notification template overrides."""
    return Blueprint(
        "oarepo_communities_notifications",
        __name__,
        template_folder=Path(__file__).parent.parent / "templates",
    )
