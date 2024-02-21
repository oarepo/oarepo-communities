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
    """RDM community's records resource."""

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        def p(route):
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        url_rules = [
            route("GET", p(routes["list"]), self.search),
            route("GET", p(routes["list-draft"]), self.search_drafts),
            route("POST", p(routes["list"]), self.create_in_community),
            # route("DELETE", p(routes["list"]), self.delete),
            # route("POST", p(routes["item"]), self.community_submission)
        ]

        return url_rules

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over the community's records."""
        hits = self.service.search(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            params=resource_requestctx.args,
            search_preference=search_preference(),
        )
        return hits.to_dict(), 200

    """
    @request_view_args
    @response_handler()
    @request_data
    def delete(self):
        errors = self.service.delete(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
        )
        response = {}
        if errors:
            response["errors"] = errors
        return response, 200
    """

    @request_view_args
    @response_handler()
    @request_data
    def create_in_community(self):
        item = self.service.create_in_community(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
        )

        return item.to_dict(), 201

    """
    @request_view_args
    @response_handler()
    @request_data
    def community_submission(self):
        item = self.service.community_submission(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            record_id=resource_requestctx.view_args["record_id"]
        )

        return item.to_dict(), 201
    """

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search_drafts(self):
        hits = self.service.search_drafts(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            params=resource_requestctx.args,
            search_preference=search_preference(),
        )
        return hits.to_dict(), 200
