from invenio_db import db

from oarepo_communities.records.models import CommunityWorkflowModel
from oarepo_communities.utils import community_id_from_record


def community_default_workflow(default, **kwargs):
    if "record" not in kwargs and "community_id" not in kwargs:
        return default
    if "community_id" not in kwargs:
        community_id = community_id_from_record(kwargs["record"])
        if not community_id:
            return default
    else:
        community_id = kwargs["community_id"]
    res = (
        db.session.query(CommunityWorkflowModel.workflow)
        .filter(CommunityWorkflowModel.community_id == community_id)
        .one()
    )
    return res[0]
