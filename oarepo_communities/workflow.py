from invenio_communities.communities.records.api import Community

from oarepo_communities.utils import community_id_from_record


def community_default_workflow(**kwargs):
    if "record" not in kwargs and "data" not in kwargs:
        return None
    if "record" in kwargs:
        community_id = community_id_from_record(kwargs["record"])
        if not community_id:
            return None
    else:
        try:
            community_id = kwargs["data"]["parent"]["communities"]["default"]
        except KeyError:
            return None

    community = Community.get_record(community_id)
    return community.custom_fields.get("workflow", "default")
