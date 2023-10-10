from invenio_communities.communities.records.api import Community as InvenioCommunityRecord
from flask import current_app

def get_field(record_class):
    if str(record_class).find("invenio_communities.communities.records.api.Community") > 0:
        return "custom_fields", current_app.config["COMMUNITIES_CUSTOM_FIELDS"]
    return None