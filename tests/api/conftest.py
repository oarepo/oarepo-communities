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
import logging
import uuid

import pytest
from flask import url_for
from invenio_accounts.testutils import create_test_user
from invenio_app.factory import create_api
from invenio_records import Record
from invenio_search import current_search, RecordsSearch
from oarepo_communities.api import OARepoCommunity
from oarepo_communities.handlers import CommunityHandler
from oarepo_communities.search import CommunitySearch
from tests.api.helpers import gen_rest_endpoint, make_sample_record, LiteEntryPoint

logging.basicConfig()
logging.getLogger('elasticsearch').setLevel(logging.DEBUG)


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    app_config['RECORDS_REST_ENDPOINTS'] = {
        'recid': gen_rest_endpoint('recid', CommunitySearch, 'tests.api.helpers.TestRecord', '<community_id>/records-anonymous')
    }
    return app_config


def extra_entrypoints(app, group=None, name=None):
    data = {
        'oarepo_enrollments.enrollments': [
            LiteEntryPoint('communities', CommunityHandler),
        ],
    }

    names = data.keys() if name is None else [name]
    for key in names:
        for entry_point in data[key]:
            yield entry_point


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


@pytest.fixture()
def sample_records(app, db, es_clear):
    try:
        current_search.client.indices.delete('records-record-v1.0.0')
    except:
        pass
    if 'records-record' not in current_search.mappings:
        current_search.register_mappings('records', 'tests.api.mappings')
    list(current_search.delete())
    list(current_search.create())
    records = {
        'A': [
            make_sample_record(db, 'Test 1 in community A', 'A', 'published'),
            make_sample_record(db, 'Test 2 in community A', 'A'),
            make_sample_record(db, 'Test 3 in community A', 'A')
        ],
        'B': [
            make_sample_record(db, 'Test 4 in community B', 'B', 'published'),
            make_sample_record(db, 'Test 5 in community B', 'B'),
            make_sample_record(db, 'Test 6 in community B', 'B'),
        ]
    }
    current_search.flush_and_refresh('records-record-v1.0.0')
    return records
