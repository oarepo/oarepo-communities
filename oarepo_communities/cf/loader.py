from flask import current_app


def get_field(record_class):
    if (
        str(record_class).find("invenio_communities.communities.records.api.Community")
        > 0
        and "COMMUNITIES_CUSTOM_FIELDS" in current_app.config
    ):
        return current_app.config["COMMUNITIES_CUSTOM_FIELDS"]
    return None
