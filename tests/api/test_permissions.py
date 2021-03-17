# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import g
from flask_principal import UserNeed
from flask_security import login_user, logout_user
from invenio_access import Permission, ActionRoles, action_factory, ParameterizedActionNeed, ActionSystemRoles
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore
from oarepo_fsm.permissions import require_any, require_all

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.constants import COMMUNITY_REQUEST_APPROVAL, COMMUNITY_APPROVE, COMMUNITY_REQUEST_CHANGES, \
    COMMUNITY_REVERT_APPROVE, COMMUNITY_PUBLISH, COMMUNITY_UNPUBLISH, COMMUNITY_READ, COMMUNITY_CREATE, \
    COMMUNITY_UPDATE, STATE_EDITING, STATE_PENDING_APPROVAL
from oarepo_communities.permissions import community_record_owner, create_object_permission_impl, \
    update_object_permission_impl
from oarepo_communities.proxies import current_oarepo_communities


def test_permissions(permissions, community, sample_records):
    """Test community permissions."""
    perms = {a: ParameterizedActionNeed(a, community[1].id) for a in current_oarepo_communities.allowed_actions}

    member = OARepoCommunity.get_role(community[1], 'member')
    curator = OARepoCommunity.get_role(community[1], 'curator')
    publisher = OARepoCommunity.get_role(community[1], 'publisher')

    # Test author community member can only request approval only in a concrete community.
    author_identity = get_identity(permissions['author'])
    assert permissions['author'].roles == [member]
    assert Permission(perms[COMMUNITY_REQUEST_APPROVAL]).allows(author_identity)
    assert not any(
        [Permission(perms[p]).allows(author_identity) for p in perms.keys() if p != COMMUNITY_REQUEST_APPROVAL])
    assert not Permission(ParameterizedActionNeed(COMMUNITY_REQUEST_APPROVAL, 'B')).allows(author_identity)
    assert not any(
        [Permission(ParameterizedActionNeed(COMMUNITY_REQUEST_APPROVAL, 'B')).allows(author_identity) for p in
         perms.keys() if
         p != COMMUNITY_REQUEST_APPROVAL])

    # Test community curator action permissions
    curator_identity = get_identity(permissions['curator'])
    assert set(permissions['curator'].roles) == {member, curator}
    assert Permission(perms[COMMUNITY_APPROVE]).allows(curator_identity)
    assert Permission(perms[COMMUNITY_REQUEST_CHANGES]).allows(curator_identity)
    assert not Permission(ParameterizedActionNeed(COMMUNITY_APPROVE, 'B')).allows(curator_identity)
    assert not any([Permission(perms[p]).allows(curator_identity) for p in perms.keys() if
                    p not in [COMMUNITY_APPROVE, COMMUNITY_REQUEST_CHANGES, COMMUNITY_REVERT_APPROVE]])

    # Test community publisher action permissions
    publisher_identity = get_identity(permissions['publisher'])
    assert set(permissions['publisher'].roles) == {member, publisher}
    assert Permission(perms[COMMUNITY_PUBLISH]).allows(publisher_identity)
    assert Permission(perms[COMMUNITY_UNPUBLISH]).allows(publisher_identity)
    assert not Permission(ParameterizedActionNeed(COMMUNITY_PUBLISH, 'B')).allows(publisher_identity)
    assert not any([Permission(perms[p]).allows(publisher_identity) for p in perms.keys() if
                    p not in [COMMUNITY_PUBLISH, COMMUNITY_UNPUBLISH, COMMUNITY_REVERT_APPROVE]])


def test_action_needs(app, db, community, community_curator):
    """Test action needs creation."""
    role = current_datastore.find_role('community:comtest:member')
    current_datastore.add_role_to_user(community_curator, role)

    ar = ActionRoles(action=COMMUNITY_READ, argument=community[1].id, role=role)
    db.session.add(ar)
    db.session.commit()

    login_user(community_curator)

    assert Permission(ParameterizedActionNeed(COMMUNITY_READ, community[1].id)).can()


def test_create_object_factory(community, users, community_member, sample_records):
    logout_user()

    community[1].allow_action(OARepoCommunity.get_role(community[1], 'member'), COMMUNITY_CREATE)

    # AnonymousUser cannot
    assert not create_object_permission_impl(record=None, community_id=community[0]).can()

    # Member can create
    login_user(community_member)
    assert create_object_permission_impl(record=None, community_id=community[0]).can()


def test_update_object_factory(community, users, community_member, community_curator, sample_records):
    logout_user()

    community[1].allow_action(OARepoCommunity.get_role(community[1], 'curator'), COMMUNITY_UPDATE)

    # AnonymousUser cannot update
    for state, rec in sample_records[community[0]][1].items():
        perm = update_object_permission_impl
        assert not perm(record=rec.record).can()

    # Member cannot update
    login_user(community_member)
    for state, rec in sample_records[community[0]][1].items():
        perm = update_object_permission_impl
        assert not perm(record=rec.record).can()

    # Curator can update filling or approving
    login_user(community_curator)
    for state, rec in sample_records[community[0]][1].items():
        perm = update_object_permission_impl
        if state in {STATE_PENDING_APPROVAL, STATE_EDITING}:
            assert perm(record=rec.record).can()
        else:
            assert not perm(record=rec.record).can()

    # Owner can update filling only


def test_owner_permissions(app, db, community, authenticated_user):
    """Test owner system role permissions."""
    login_user(authenticated_user)
    assert len(g.identity.provides) == 4
    assert community_record_owner in g.identity.provides

    permissions = require_any(
        # Approval is granted either by user role
        Permission(ParameterizedActionNeed(COMMUNITY_REQUEST_APPROVAL, community[0])),
        require_all(
            # Or user id must match and record owners must be granted the action
            Permission(UserNeed(authenticated_user.id)),
            Permission(ParameterizedActionNeed(f'owner-{COMMUNITY_REQUEST_APPROVAL}', community[0]))
        )
    )

    assert not permissions().can()

    db.session.add(
        ActionSystemRoles(action=f'owner-{COMMUNITY_REQUEST_APPROVAL}', role_name=community_record_owner.value,
                          argument=community[0]))

    assert permissions().can()
