# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from oarepo_communities.api import OARepoCommunity


def _check_community(comm, community_ext_groups):
    assert comm.members_id == community_ext_groups['members_id']
    assert comm.curators_id == community_ext_groups['curators_id']
    assert comm.publishers_id == community_ext_groups['publishers_id']
    assert comm.json == {'title': 'Title', 'description': 'Community description'}


def test_integrity(community, community_ext_groups):
    # Community id code cannot be reused
    with pytest.raises(FlushError):
        OARepoCommunity.create({},
                               uuid.uuid4(), uuid.uuid4(), uuid.uuid4(),
                               id_=community[0])

    # Single members group cannot be in multiple communities
    with pytest.raises(IntegrityError):
        OARepoCommunity.create({},
                               community_ext_groups['members_id'], uuid.uuid4(), uuid.uuid4(),
                               id_='another-community')

    # Single group of curators can be assigned to multiple communities
    OARepoCommunity.create({},
                           uuid.uuid4(), community_ext_groups['curators_id'], uuid.uuid4(),
                           id_='another-community')

    # Single group of publishers can be assigned to multiple communities
    OARepoCommunity.create({},
                           uuid.uuid4(), uuid.uuid4(), community_ext_groups['publishers_id'],
                           id_='just-another-community')


def test_community_model(community, community_ext_groups):
    """Test OARepo community model."""
    comid, comm = community
    assert comid == comm.id == 'comtest'
    _check_community(comm, community_ext_groups)


def test_get_community(community, community_ext_groups):
    comm = OARepoCommunity.get_community('comtest')
    assert comm is not None
    _check_community(comm, community_ext_groups)


def test_get_communities(community, community_ext_groups):
    comms = OARepoCommunity.get_communities(['comtest'])
    assert comms is not None
    assert len(comms) == 1
    _check_community(comms[0], community_ext_groups)
