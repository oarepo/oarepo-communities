from invenio_db import db

from oarepo_communities.records.models import CommunityWorkflowModel


def community_default_workflow(default, **kwargs):
    if "record" not in kwargs and "community_id" not in kwargs:
        return default
    if "community_id" not in kwargs:
        record = kwargs["record"]
        try:
            community_id = str(record.communities.default.id)
        except AttributeError:
            return default
    else:
        community_id = kwargs["community_id"]
    res = (
        db.session.query(CommunityWorkflowModel.workflow)
        .filter(CommunityWorkflowModel.community_id == community_id)
        .one()
    )
    return res[0]
