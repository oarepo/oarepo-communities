# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from oarepo_communities import OARepoCommunities


def test_community_model(community, community_ext_groups):
    """Test OARepo community model."""
    comid, comm = community
    assert comid == comm.id == 'comtest'
    assert comm.model.members_id == community_ext_groups['members_id']
    assert comm.model.curators_id == community_ext_groups['curators_id']
    assert comm.model.publishers_id == community_ext_groups['publishers_id']
    assert comm.model.json['title'] == 'Title'
