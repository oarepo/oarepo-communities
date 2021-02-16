# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import uuid

import pytest
from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from sqlalchemy.orm.exc import FlushError

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.models import OARepoCommunityModel


def _check_community(comm, community_ext_groups):
    assert comm.members_id == current_datastore.find_role(community_ext_groups['members_id']).id
    assert comm.curators_id == current_datastore.find_role(community_ext_groups['curators_id']).id
    assert comm.publishers_id == current_datastore.find_role(community_ext_groups['publishers_id']).id
    assert comm.json == {'title': 'Title', 'description': 'Community description'}


def test_integrity(community, community_roles):
    # Community id code cannot be reused
    with pytest.raises(FlushError):
        OARepoCommunity.create({},
                               uuid.uuid4(), uuid.uuid4(), uuid.uuid4(),
                               id_=community[0])


def test_community_model(community, community_ext_groups):
    """Test OARepo community model."""
    comid, comm = community
    assert comid == comm.id == 'comtest'
    _check_community(comm, community_ext_groups['A'])


def test_get_community(community, community_ext_groups):
    comm = OARepoCommunity.get_community('comtest')
    assert comm is not None
    _check_community(comm, community_ext_groups['A'])


def test_get_communities(community, community_ext_groups):
    comms = OARepoCommunity.get_communities(['comtest'])
    assert comms is not None
    assert len(comms) == 1
    _check_community(comms[0], community_ext_groups['A'])


def test_get_community_from_role(community, community_roles, community_ext_groups):
    rol = Role.query.get(community_roles['A']['members_id'])
    comm = rol.oarepo_community.one_or_none()

    assert comm is not None
    _check_community(comm, community_ext_groups['A'])

    rol = Role.query.get(community_roles['A']['curators_id'])
    comm = rol.curators_oarepo_community.one_or_none()
    assert comm is not None
    _check_community(comm, community_ext_groups['A'])

    rol = Role.query.get(community_roles['A']['publishers_id'])
    comm = rol.publishers_oarepo_community.one_or_none()
    assert comm is not None
    _check_community(comm, community_ext_groups['A'])

    comm2 = OARepoCommunity.get_community_from_role(rol)
    assert comm2 is not None
    assert comm2 == comm

    # Test role not bound to community
    rol = Role.query.get(community_roles['B']['members_id'])
    comm = rol.oarepo_community.one_or_none()
    assert comm is None

    comm2 = OARepoCommunity.get_community_from_role(rol)
    assert comm2 is None


def test_community_delete(community):
    rols = Role.query.all()
    assert len(rols) == 6

    db.session.delete(community[1])
    db.session.commit()
    coms = OARepoCommunityModel.query.all()
    assert len(coms) == 0

    rols = Role.query.all()
    assert len(rols) == 3
