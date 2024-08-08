from invenio_db import db
from sqlalchemy.exc import NoResultFound

from oarepo_communities.records.models import CommunityWorkflowModel
from oarepo_communities.utils import community_id_from_record
from invenio_communities.communities.records.api import Community

def community_default_workflow(**kwargs):
    if "record" not in kwargs and "community_id" not in kwargs:
        return None
    if "community_id" not in kwargs:
        community_id = community_id_from_record(kwargs["record"])
        if not community_id:
            return None
    else:
        community_id = kwargs["community_id"]

    community = Community.get_record(community_id)
    return community.custom_fields.get("workflow")