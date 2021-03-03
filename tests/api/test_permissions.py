# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask_principal import ActionNeed
from flask_security import login_user
from invenio_access import Permission, ActionRoles
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.permissions import action2need_map, Read, COMMUNITY_READ


def test_permissions(permissions, community, sample_records):
    """Test community permissions."""

    perms = {a: p(community[1].id) for a, p in action2need_map.items()}

    member = OARepoCommunity.get_role(community[1], 'member')
    curator = OARepoCommunity.get_role(community[1], 'curator')
    publisher = OARepoCommunity.get_role(community[1], 'publisher')

    # Test author community member can only request approval only in a concrete community.
    author_identity = get_identity(permissions['author'])
    assert permissions['author'].roles == [member]
    assert Permission(perms['request-approval']).allows(author_identity)
    assert not any([Permission(perms[p]).allows(author_identity) for p in perms.keys() if p != 'request-approval'])
    assert not Permission(action2need_map['request-approval']('B')).allows(author_identity)
    assert not any(
        [Permission(action2need_map['request-approval']('B')).allows(author_identity) for p in perms.keys() if
         p != 'request-approval'])

    # Test community curator action permissions
    curator_identity = get_identity(permissions['curator'])
    assert set(permissions['curator'].roles) == {member, curator}
    assert Permission(perms['approve']).allows(curator_identity)
    assert Permission(perms['request-changes']).allows(curator_identity)
    assert not Permission(action2need_map['approve']('B')).allows(curator_identity)
    assert not any([Permission(perms[p]).allows(curator_identity) for p in perms.keys() if
                    p not in ['approve', 'request-changes', 'revert-approve']])

    # Test community publisher action permissions
    publisher_identity = get_identity(permissions['publisher'])
    assert set(permissions['publisher'].roles) == {member, publisher}
    assert Permission(perms['publish']).allows(publisher_identity)
    assert Permission(perms['unpublish']).allows(publisher_identity)
    assert not Permission(action2need_map['publish']('B')).allows(publisher_identity)
    assert not any([Permission(perms[p]).allows(publisher_identity) for p in perms.keys() if
                    p not in ['publish', 'unpublish', 'revert-approve']])


def test_action_needs(app, db, community, community_curator):
    """Test action needs creation."""
    role = current_datastore.find_role('community:comtest:member')
    current_datastore.add_role_to_user(community_curator, role)

    ar = ActionRoles(action=COMMUNITY_READ, argument=community[1].id, role=role)
    db.session.add(ar)
    db.session.commit()

    login_user(community_curator)

    assert Permission(ActionNeed(COMMUNITY_READ, community[1].id)).can()
