# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_access import Permission
from invenio_access.utils import get_identity
from invenio_accounts.models import Role

from oarepo_communities.permissions import _action2need_map


def test_permissions(permissions, community, sample_records):
    """Test community permissions."""

    perms = {a: p(community[1].id) for a, p in _action2need_map.items()}

    member = Role.query.get(1)

    # Test author community member can only request approval only in a concrete community.
    author_identity = get_identity(permissions['author'])
    assert permissions['author'].roles == [member]
    assert Permission(perms['request-approval']).allows(author_identity)
    assert not any([Permission(perms[p]).allows(author_identity) for p in perms.keys() if p != 'request-approval'])
    assert not Permission(_action2need_map['request-approval']('B')).allows(author_identity)
    assert not any(
        [Permission(_action2need_map['request-approval']('B')).allows(author_identity) for p in perms.keys() if
         p != 'request-approval'])

    # Test community curator action permissions
    curator_identity = get_identity(permissions['curator'])

