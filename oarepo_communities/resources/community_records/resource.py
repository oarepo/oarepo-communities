from flask import g
from flask_resources import resource_requestctx, response_handler, route
from invenio_drafts_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference


class CommunityRecordsResource(RecordResource):
    """Communities-specific records resource."""

    def create_url_rules(self) -> list[dict]:
        """Create the URL rules for the record resource."""

        def p(route) -> str:
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        url_rules = [
            route("POST", p(routes["list"]), self.create_in_community),
            route(
                "POST",
                p(routes["list-model"]),
                self.create_in_community,
                endpoint="create_in_community_with_model",
            )
        ]

        return url_rules


    @request_view_args
    @response_handler()
    @request_data
    def create_in_community(self) -> tuple[dict, int]:
        model = (
            resource_requestctx.view_args["model"]
            if "model" in resource_requestctx.view_args
            else None
        )
        item = self.service.create(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
            model=model,
        )

        return item.to_dict(), 201