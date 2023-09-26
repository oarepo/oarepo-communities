from invenio_communities.communities.records.api import Community as InvenioCommunityRecord
from flask import current_app

def get_field(record_class):
    if str(record_class).find("invenio_communities.communities.records.api.Community") > 0:
        custom_field = getattr(record_class, "custom_fields")
        return None, current_app.config[custom_field.config_key]
    return None