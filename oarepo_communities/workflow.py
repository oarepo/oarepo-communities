from invenio_communities.communities.records.api import Community

from oarepo_communities.utils import community_id_from_record


def community_default_workflow(**kwargs):
    # optimization: if community metadata is passed, use it
    if "community_metadata" in kwargs:
        community_metadata = kwargs["community_metadata"]
        custom_fields = community_metadata.json.get('custom_fields', {})
        return custom_fields.get("workflow", "default")

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

    # use pid resolve so that the community might be both slug or id
    community = Community.pid.resolve(community_id)
    return community.custom_fields.get("workflow", "default")
