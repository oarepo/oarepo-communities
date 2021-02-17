# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask_babelex import gettext
from invenio_accounts.models import Role
from invenio_db import db
from invenio_records.models import Timestamp
from speaklater import make_lazy_gettext
from sqlalchemy import event
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType, ChoiceType

from oarepo_communities.config import OAREPO_COMMUNITIES_ROLES
from oarepo_communities.utils import community_role_kwargs

_ = make_lazy_gettext(lambda: gettext)

OAREPO_COMMUNITIES_TYPES = [
    ('wgroup', _('Working group')),
    ('project', _('Project')),
    ('rgroup', _('Research group')),
    ('other', _('Other'))
]
"""Community types or focus."""


class OARepoCommunityModel(db.Model, Timestamp):
    __tablename__ = 'oarepo_communities'
    __table_args__ = {'extend_existing': True}
    __versioned__ = {'versioning': False}

    id = db.Column(
        db.String(63),
        primary_key=True,
    )
    """Primary Community identifier slug."""

    title = db.Column(
        db.String(128),
    )
    """Community title name."""

    type = db.Column(ChoiceType(choices=OAREPO_COMMUNITIES_TYPES, impl=db.CHAR(16)),
                     default='other', nullable=False)
    """Community type or focus."""

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

    @property
    def roles(self):
        """Return roles associated with this community."""
        role_names = []
        for name in [community_role_kwargs(self, r)['name'] for r in OAREPO_COMMUNITIES_ROLES]:
            role_names.append(name)

        with db.session.no_autoflush:
            query = Role.query.filter(Role.name.in_(role_names))
            return query.all()

    def delete_roles(self):
        """Delete roles associated with this community."""
        with db.session.begin_nested():
            for r in self.roles:
                db.session.delete(r)

    def delete(self):
        """Mark the community for deletion."""
        self.is_deleted = True
        self.delete_roles()


@event.listens_for(OARepoCommunityModel, 'before_delete')
def handle_before_delete(mapper, connection, target):
    target.delete()
