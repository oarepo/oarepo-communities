from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin

if TYPE_CHECKING:
    from flask_resources import ResponseHandler


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    blueprint_name = "oarepo-community-records"
    url_prefix = "/communities/"
    routes = {
        "list": "<pid_value>/records",
        "list-model": "<pid_value>/<model>",
    }
    request_view_args = {
        **RecordResourceConfig.request_view_args,
        "model": ma.fields.Str(),
    }
