# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import uuid

import pytest
from invenio_access import ActionRoles
from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from sqlalchemy.orm.exc import FlushError

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.proxies import current_oarepo_communities


def _check_community(comm):
    assert comm.json == {'description': 'Community description'}
    assert comm.type == 'other'
    assert comm.title == 'Title'

def test_integrity(community):
    # Community id code cannot be reused
    with pytest.raises(FlushError):
        OARepoCommunity.create({}, id_=community[0], title=community[1].title)


def test_community_model(community):
    """Test OARepo community model."""
    comid, comm = community
    assert comid == comm.id == 'comtest'
    _check_community(comm)


def test_community_create(db):
    comm = OARepoCommunity.create(
        {'description': 'Community description'},
        id_='comtest',
        title='Title',
    )
    _check_community(comm)
    ar = ActionRoles.query.filter_by(argument=comm.id).all()
    assert len(ar) == 0


def test_get_community(community, community_ext_groups):
    comm = OARepoCommunity.get_community('comtest')
    assert comm is not None
    _check_community(comm)


def test_get_communities(community):
    comms = OARepoCommunity.get_communities(['comtest'])
    assert comms is not None
    assert len(comms) == 1
    _check_community(comms[0])


def test_get_community_from_role(community):
    rol = current_datastore.find_role(f'community:{community[1].id}:member')
    assert rol is not None

    comm = rol.community.one_or_none()
    assert comm is not None
    assert comm == community[1]

    # Test role not bound to community
    rol = current_datastore.create_role(name='other')
    comm2 = rol.community.one_or_none()
    assert comm2 is None


def test_community_roles(community):
    assert len(community[1].roles) == 3


def test_community_delete(community):
    rols = Role.query.all()
    assert len(rols) == 3

    db.session.delete(community[1])
    db.session.commit()
    coms = OARepoCommunityModel.query.all()
    assert len(coms) == 0

    rols = Role.query.all()
    assert len(rols) == 0
