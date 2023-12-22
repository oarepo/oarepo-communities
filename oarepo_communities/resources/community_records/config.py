from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin
import marshmallow as ma


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    # blueprint_name = "community-records"
    # url_prefix = "/communities"
    routes = {
        "list": "/<pid_value>/records",
        "list-draft": "/<pid_value>/draft/records",
        "item": "/<pid_value>/records/<record_id>"
    }

    request_view_args = {
        **RecordResourceConfig.request_view_args,
        "record_id": ma.fields.Str(),
    }
