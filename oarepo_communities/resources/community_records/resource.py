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

from flask import g
from flask_resources import resource_requestctx, response_handler, route
from invenio_drafts_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_view_args,
)


class CommunityRecordsResource(RecordResource):
    """Communities-specific records resource."""

    def create_url_rules(self) -> list[dict]:
        """Create the URL rules for the record resource."""

        def p(route: str) -> str:
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        return [
            route("POST", p(routes["list"]), self.create_in_community),
            route(
                "POST",
                p(routes["list-model"]),
                self.create_in_community,
                endpoint="create_in_community_with_model",
            ),
        ]

    @request_view_args
    @response_handler()
    @request_data
    def create_in_community(self) -> tuple[dict, int]:
        """Create a record in a community."""
        model = resource_requestctx.view_args.get("model", None)
        item = self.service.create(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
            model=model,
        )

        return item.to_dict(), 201
