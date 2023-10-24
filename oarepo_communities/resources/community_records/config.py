from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin


class CommunityRecordsResourceConfig(RecordResourceConfig, ConfiguratorMixin):
    """Community's records resource config."""

    # blueprint_name = "community-records"
    # url_prefix = "/communities"
    routes = {"list": "/<pid_value>/records"}
