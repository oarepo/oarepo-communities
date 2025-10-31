#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module for community records related resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin

if TYPE_CHECKING:
    from collections.abc import Mapping


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    blueprint_name = "oarepo-community-records"
    url_prefix = "/communities/"
    routes: Mapping[str, str] = {
        "list": "<pid_value>/records",
        "list-model": "<pid_value>/<model>",
    }
    request_view_args: Mapping[str, ma.fields.Field] = {
        **RecordResourceConfig.request_view_args,
        "model": ma.fields.Str(),
    }
