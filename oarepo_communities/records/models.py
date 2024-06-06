from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types import UUIDType


class CommunityWorkflowModel(db.Model):
    __versioned__ = {}
    __tablename__ = "community_scenario"

    @declared_attr
    def community_id(cls):
        """Foreign key to the related communithy."""
        return db.Column(
            UUIDType,
            db.ForeignKey(CommunityMetadata.id, ondelete="CASCADE"),
            primary_key=True,
        )

    workflow = db.Column(String)


class RecordWorkflowModelMixin:
    __record_model__ = None

    @declared_attr
    def record_id(cls):
        """Foreign key to the related record."""
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model__.id, ondelete="CASCADE"),
            primary_key=True,
        )

    workflow = db.Column(String)
