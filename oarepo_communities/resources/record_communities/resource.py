
from flask import abort, current_app, g, send_file
from flask_cors import cross_origin
from flask_resources import (
    HTTPJSONException,
    Resource,
    ResponseHandler,
    from_conf,
    request_parser,
    resource_requestctx,
    response_handler,
    route,
    with_content_negotiation,
)

from invenio_records_resources.resources.errors import ErrorHandlersMixin
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_extra_args,
    request_headers,
    request_read_args,
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference


class RecordCommunitiesResource(ErrorHandlersMixin, Resource):
    """Record communities resource."""

    def __init__(self, config, service):
        """Constructor."""
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create the URL rules for the record resource."""
        routes = self.config.routes
        url_rules = [
            route("GET", routes["list"], self.search),
            route("POST", routes["list"], self.add_to_published_record),
            route("POST", routes["draft-list"], self.add_to_draft),
            route("DELETE", routes["list"], self.remove),
        ]
        return url_rules

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Search for record's communities."""
        items = self.service.search(
            identity=g.identity,
            id_=resource_requestctx.view_args["pid_value"],
            params=resource_requestctx.args,
            search_preference=search_preference(),
            expand=resource_requestctx.args.get("expand", False),
        )
        return items.to_dict(), 200

    @request_view_args
    @response_handler()
    @request_data
    def add_to_published_record(self):
        """Include record in communities."""
        processed, errors = self.service.add_to_published_record(
            identity=g.identity,
            id_=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
        )

        response = {}
        if processed:
            response["processed"] = processed
        if errors:
            response["errors"] = errors

        # TODO why not checking errors
        return response, 200 if len(processed) > 0 else 400

    @request_view_args
    @response_handler()
    @request_data
    def add_to_draft(self):
        """Include record in communities."""
        processed, errors = self.service.add_to_draft(
            identity=g.identity,
            id_=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
        )

        response = {}
        if processed:
            response["processed"] = processed
        if errors:
            response["errors"] = errors

        # TODO why not checking errors
        return response, 200 if len(processed) > 0 else 400

    @request_view_args
    @request_data
    @response_handler()
    def remove(self):
        """Remove communities from the record."""
        processed, errors = self.service.remove(
            identity=g.identity,
            id_=resource_requestctx.view_args["pid_value"],
            data=resource_requestctx.data,
        )

        response = {}
        if errors:
            response["errors"] = errors

        return response, 200 if len(processed) > 0 else 400