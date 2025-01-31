from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin
from oarepo_global_search.proxies import current_global_search

if TYPE_CHECKING:
    from flask_resources import ResponseHandler


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    blueprint_name = "oarepo-community-records"
    url_prefix = "/communities/"
    routes = {
        "list": "<pid_value>/records",
        "list-model": "<pid_value>/<model>",
        "list-user": "<pid_value>/user/records",
        "list-user-model": "<pid_value>/user/<model>",
    }
    request_view_args = {
        **RecordResourceConfig.request_view_args,
        "model": ma.fields.Str(),
    }

    # todo - if service isn't in global search services but needs to be used here - ask whether this can happen
    # then we would need to look at another configuration
    @property
    def response_handlers(self) -> dict[str, ResponseHandler]:
        return {
            **current_global_search.global_search_resource.config.response_handlers,
            **super().response_handlers,
        }
