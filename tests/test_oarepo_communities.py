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


def test_get_primary_community_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_PRIMARY_COMMUNITY_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.get_primary_community_field(data)
    assert a == "ham"


def test_set_primary_community_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_PRIMARY_COMMUNITY_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.set_primary_community_field(data, "blah")
    assert a == {'spam': 'blah'}


def test_get_owned_by_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_OWNED_BY_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.get_owned_by_field(data)
    assert a == "ham"


def test_set_owned_by_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_OWNED_BY_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.set_owned_by_field(data, "blah")
    assert a == {'spam': 'blah'}

def test_get_communities_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_COMMUNITIES_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.get_communities_field(data)
    assert a == "ham"


def test_set_communities_field():
    data = {
        "bla": {"spam": "ham"}
    }
    app = Flask('testapp')
    app.config["OAREPO_COMMUNITIES_COMMUNITIES_FIELD"] = "bla.spam"
    OARepoCommunities(app)
    state = app.extensions['oarepo-communities']
    a = state.set_communities_field(data, "blah")
    assert a == {'spam': 'blah'}
