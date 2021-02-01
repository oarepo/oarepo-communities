# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from oarepo_communities import OARepoCommunities


def test_version():
    """Test version import."""
    from oarepo_communities import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = OARepoCommunities(app)
    assert 'oarepo-communities' in app.extensions

    app = Flask('testapp')
    ext = OARepoCommunities()
    assert 'oarepo-communities' not in app.extensions
    ext.init_app(app)
    assert 'oarepo-communities' in app.extensions

