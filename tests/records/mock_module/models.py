# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Example of a record/community database model."""

from invenio_communities.records.records.models import CommunityRelationMixin
from invenio_db import db
from invenio_records.models import RecordMetadataBase


class MockRecordMetadata(db.Model, RecordMetadataBase):
    """A basic record metadata model."""

    __tablename__ = 'mock_record_metadata'


class MockRecordCommunity(db.Model, CommunityRelationMixin):
    """Relationship model between record and community."""

    __tablename__ = 'mock_record_community'
    __record_model__ = MockRecordMetadata
    # __request_model__ = RequestMetadata
