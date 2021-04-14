# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from functools import partial

import pytest

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.signals import after_community_insert, before_community_insert


@pytest.fixture()
def signals():
    """Fixtures to connect signals."""
    called = {}

    def _listener(signal_name, sender, *args, **kwargs):
        if signal_name not in called:
            called[signal_name] = {**kwargs}
        called[signal_name].update(**kwargs)

    before_community_insert_listener = partial(_listener, 'before_community_insert')
    after_community_insert_listener = partial(_listener, 'after_community_insert')
    after_community_insert.connect(after_community_insert_listener)
    before_community_insert.connect(before_community_insert_listener)

    yield called


def test_signals(base_app, db, signals):
    com = OARepoCommunity.create({}, id_='signals-community', title='Signals comm')

    assert 'before_community_insert' in signals
    assert 'after_community_insert' in signals
    assert len(signals.keys()) == 2

    assert 'community' in signals['after_community_insert'].keys()
    assert signals['after_community_insert']['community'] == com

    assert 'community' in signals['before_community_insert'].keys()
    assert signals['before_community_insert']['community'] == com
