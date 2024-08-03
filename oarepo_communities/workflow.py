from invenio_db import db
from sqlalchemy.exc import NoResultFound

from oarepo_communities.records.models import CommunityWorkflowModel
from oarepo_communities.utils import community_id_from_record


def community_default_workflow(**kwargs):
    if "record" not in kwargs and "community_id" not in kwargs:
        return None
    if "community_id" not in kwargs:
        community_id = community_id_from_record(kwargs["record"])
        if not community_id:
            return None
    else:
        community_id = kwargs["community_id"]
    try:
        res = (
            db.session.query(CommunityWorkflowModel.workflow)
            .filter(CommunityWorkflowModel.community_id == community_id)
            .one()
        )
    except NoResultFound:
        return None
    return res[0]
