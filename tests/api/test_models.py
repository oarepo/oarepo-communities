# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
from oarepo_communities.api import OARepoCommunity


def _check_community(comm, community_ext_groups):
    assert comm.members_id == community_ext_groups['members_id']
    assert comm.curators_id == community_ext_groups['curators_id']
    assert comm.publishers_id == community_ext_groups['publishers_id']
    assert comm.json == {'title': 'Title', 'description': 'Community description'}


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
