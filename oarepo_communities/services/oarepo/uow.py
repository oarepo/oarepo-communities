from invenio_db import db
from invenio_records_resources.services.uow import Operation
from sqlalchemy.exc import NoResultFound

from oarepo_communities.records.models import CommunityWorkflowModel


class CommunityWorkflowCommitOp(Operation):
    """Featured community add/update operation."""

    def __init__(self, community_id, workflow):
        """Initialize the commit operation."""
        super().__init__()
        self._community_id = community_id
        self._workflow = workflow

    def on_register(self, uow):
        try:
            record = CommunityWorkflowModel.query.filter(
                CommunityWorkflowModel.community_id == self._community_id
            ).one()
            record.query.update({"workflow": self._workflow})
            db.session.commit()
        except NoResultFound:
            obj = CommunityWorkflowModel(
                community_id=str(self._community_id),
                workflow=self._workflow,
            )
            db.session.add(obj)
