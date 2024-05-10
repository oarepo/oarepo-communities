from invenio_communities.proxies import current_communities
from invenio_records.systemfields.base import SystemField


def community_entity_reference_ui_resolver(identity, reference):
    # todo kde sehnat link?
    user_id = reference["oarepo_community"]
    community_search = current_communities.service.read(identity, user_id)
    if user.username is None or isinstance(
        user.username, SystemField
    ):  # username undefined?
        label = user.email
    else:
        label = user.username
    ret = {
        "reference": reference,
        "type": "user",
        "label": label,
    }
    if "links" in user_search:
        ret["links"] = user_search["links"]
