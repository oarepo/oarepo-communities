# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_access import Permission
from invenio_access.utils import get_identity

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.permissions import action2need_map


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
