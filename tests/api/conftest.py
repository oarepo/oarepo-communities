# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
import uuid

import pytest
from invenio_accounts.testutils import create_test_user
from invenio_app.factory import create_api

from oarepo_communities.api import OARepoCommunity


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope='module')
def users(base_app):
    yield [create_test_user('user{}@inveniosoftware.org'.format(i)) for i in range(3)]


@pytest.fixture
def authenticated_user(db):
    """Authenticated user."""
    yield create_test_user('authed@inveniosoftware.org')


@pytest.fixture
def community_curator(db):
    """Curator user."""
    yield create_test_user('community-curator@inveniosoftware.org')


@pytest.fixture
def community_publisher(db):
    """Curator user."""
    yield create_test_user('community-publisher@inveniosoftware.org')


@pytest.fixture
def community_ext_groups():
    return {
        'members_id': uuid.uuid4(),
        'curators_id': uuid.uuid4(),
        'publishers_id': uuid.uuid4(),
    }


@pytest.fixture
def community(db, community_ext_groups):
    """Community fixture."""
    comid = 'comtest'
    community = OARepoCommunity.create(
        {'title': 'Title',
         'description': 'Community description'},
        **community_ext_groups,
        id_=comid)
    db.session.commit()
    yield comid, community
