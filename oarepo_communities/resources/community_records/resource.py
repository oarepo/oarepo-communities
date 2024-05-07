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
            route("GET", p(routes["list-user"]), self.search_user),
            route("POST", p(routes["list"]), self.create_in_community),
            route("POST", p(routes["list-model"]), self.create_in_community, endpoint="create_in_community_with_model")
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

    @request_view_args
    @response_handler()
    @request_data
    def create_in_community(self):
        model = resource_requestctx.view_args["model"] if "model" in resource_requestctx.view_args else None
        item = self.service.create_in_community(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
            model=model
        )

        return item.to_dict(), 201


    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search_user(self):
        hits = self.service.user_search(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            params=resource_requestctx.args,
            search_preference=search_preference(),
        )
        return hits.to_dict(), 200
