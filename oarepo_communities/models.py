# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_db import db
from invenio_records.models import Timestamp
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import UUIDType, JSONType


class OARepoCommunityModel(db.Model, Timestamp):
    __tablename__ = 'oarepo_communities'
    __table_args__ = {'extend_existing': True}
    __versioned__ = {'versioning': False}

    id = db.Column(
        db.String(64),
        primary_key=True,
    )
    """Primary Community identifier slug."""

    members_id = db.Column(
        UUIDType,
        nullable=False,
        unique=True,
        index=True
    )
    """Community members external group UUID."""

    curators_id = db.Column(
        UUIDType,
        nullable=False,
        unique=False,
        index=True
    )
    """Community curators external group UUID."""

    publishers_id = db.Column(
        UUIDType,
        nullable=False,
        unique=False,
        index=True
    )
    """Community publishers external group UUID."""

    json = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """Store community metadata in JSON format."""

    is_deleted = db.Column(
        db.Boolean(name="ck_oarepo_community_metadata_is_deleted"),
        nullable=True,
        default=False
    )
    """Was the OARepo community soft-deleted."""

    def delete(self):
        """Mark the community for deletion."""
        self.is_deleted = True
