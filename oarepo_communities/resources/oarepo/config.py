import marshmallow as ma
from flask_resources.resources import ResourceConfig


class OARepoCommunityConfig(ResourceConfig):
    """Community's records resource config."""

    blueprint_name = "oarepo-community"
    url_prefix = "/communities/"
    routes = {
        "workflow": "<pid_value>/workflow/<workflow>",
    }
    request_view_args = {"pid_value": ma.fields.Str(), "workflow": ma.fields.Str()}
