from flask import g
from flask_resources import resource_requestctx, response_handler, route
from flask_resources.resources import Resource
from invenio_records_resources.resources.records.resource import request_view_args


class OARepoCommunityResource(Resource):
    # todo This was supposed to allow changing of default workflows for community in api calls
    # but idk how that is actually planned to work, I realized that this is some kind of administration/superuser thing
    # which I don't know how it works?

    def __init__(self, config, service):
        """Constructor."""
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        routes = self.config.routes
        url_rules = [
            route("POST", routes["workflow"], self.set_community_workflow),
        ]

        return url_rules

    @request_view_args
    @response_handler()
    def set_community_workflow(self):

        result_dict = self.service.set_community_workflow(
            identity=g.identity,
            community_id=resource_requestctx.view_args["pid_value"],
            workflow=resource_requestctx.view_args["workflow"],
        )

        return result_dict, 201
