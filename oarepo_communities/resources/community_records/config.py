import marshmallow as ma
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    blueprint_name = "community-records"
    url_prefix = "/communities/"
    routes = {
        "list": "<pid_value>/records",
        "list-model":  "<pid_value>/<model>/records",
        "list-user": "<pid_value>/user/records",
        "item": "<pid_value>/records/<record_id>",
    }
    request_view_args = {
        **RecordResourceConfig.request_view_args,
        "record_id": ma.fields.Str(),
        "model": ma.fields.Str()
    }
