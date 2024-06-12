from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
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


class RecordWorkflowModelMixin:
    __record_model__ = None

    @declared_attr
    def record_id(cls):
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model__.id, ondelete="CASCADE"),
            primary_key=True,
        )

    """
    record_id = db.Column(
            UUIDType,
            db.ForeignKey(__record_model__.id, ondelete="CASCADE"),
            primary_key=True,
        )
    """

    workflow = db.Column(String)
