# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from itertools import groupby
from operator import attrgetter

from flask_babelex import gettext
from invenio_access import ActionRoles, ActionSystemRoles
from invenio_access.proxies import current_access
from invenio_db import db
from invenio_records.models import Timestamp
from speaklater import make_lazy_gettext
from sqlalchemy import event
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType, ChoiceType

from oarepo_communities.proxies import current_oarepo_communities

_ = make_lazy_gettext(lambda: gettext)

OAREPO_COMMUNITIES_TYPES = [
    ('wgroup', _('Working group')),
    ('project', _('Project')),
    ('rgroup', _('Research group')),
    ('other', _('Other'))
]
"""Community types or focus."""

oarepo_communities_role = db.Table(
    'oarepo_communities_role',
    db.Column('community_id', db.String(63), db.ForeignKey(
        'oarepo_communities.id', name='fk_oarepo_communities_role_community_id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(
        'accounts_role.id', name='fk_oarepo_communities_role_role_id'), unique=True),
)
"""Relationship between Communities and Invenio roles."""


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

    type = db.Column(ChoiceType(choices=OAREPO_COMMUNITIES_TYPES, impl=db.VARCHAR(16)),
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

    roles = db.relationship('Role', secondary=oarepo_communities_role,
                            backref=db.backref('community', lazy='dynamic'))

    def delete_roles(self):
        """Delete roles associated with this community."""
        with db.session.begin_nested():
            for r in self.roles:
                db.session.delete(r)

    def delete(self):
        """Mark the community for deletion."""
        self.is_deleted = True
        self.delete_roles()

    def _validate_role_action(self, role, action, system=False):
        if action not in current_oarepo_communities.allowed_actions:
            raise AttributeError(f'Action {action} not allowed')
        if system:
            if role.value not in current_access.system_roles:
                raise AttributeError(f'Role {role} not in system roles')
        elif role not in self.roles:
            raise AttributeError(f'Role {role} not in community roles')

    def allow_action(self, role, action, system=False):
        """Allow action for a role."""
        self._validate_role_action(role, action, system)

        with db.session.begin_nested():
            if system:
                ar = ActionSystemRoles.query.filter_by(action=action, argument=self.id, role_name=role.value).first()
                if not ar:
                    ar = ActionSystemRoles(action=action, argument=self.id, role_name=role.value)
            else:
                ar = ActionRoles.query.filter_by(action=action, argument=self.id, role_id=role.id).first()
                if not ar:
                    ar = ActionRoles(action=action, argument=self.id, role=role)

            db.session.add(ar)
            return ar

    def deny_action(self, role, action, system=False):
        """Deny action for a role."""
        self._validate_role_action(role, action, system)

        with db.session.begin_nested():
            if system:
                ar = ActionSystemRoles.query.filter_by(action=action, argument=self.id, role_name=role.value).all()
            else:
                ar = ActionRoles.query.filter_by(action=action, argument=self.id, role=role).all()
            for a in ar:
                db.session.delete(a)

    @property
    def actions(self):
        ars = ActionRoles.query \
            .filter_by(argument=self.id) \
            .order_by(ActionRoles.action).all()
        sars = ActionSystemRoles.query \
            .filter_by(argument=self.id) \
            .order_by(ActionSystemRoles.action).all()
        ars = [{k: list(g)} for k, g in groupby(ars, key=attrgetter('action'))]
        sars = [{k: list(g)} for k, g in groupby(sars, key=attrgetter('action'))]

        return ars, sars

    @property
    def excluded_facets(self):
        return self.json.get('excluded_facets', {})

    def to_json(self):
        return dict(
            id=self.id,
            title=self.title,
            type=str(self.type),
            metadata=self.json
        )


@event.listens_for(OARepoCommunityModel, 'before_delete')
def handle_before_delete(mapper, connection, target):
    target.delete()
