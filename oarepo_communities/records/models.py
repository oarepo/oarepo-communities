from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from sqlalchemy import String
from sqlalchemy_utils.types import UUIDType


class CommunityWorkflowModel(db.Model):
    __versioned__ = {}
    __tablename__ = "community_scenario"

    community_id = db.Column(
        UUIDType,
        db.ForeignKey(CommunityMetadata.id, ondelete="CASCADE"),
        primary_key=True,
    )
    workflow = db.Column(String)
