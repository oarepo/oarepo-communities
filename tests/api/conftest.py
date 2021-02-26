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
import os
import uuid

import pytest
from invenio_access import ActionRoles, ActionUsers
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import create_test_user
from invenio_app.factory import create_api
from invenio_search import current_search
from oarepo_enrollments.config import allow_all
from oarepo_enrollments.ext import OARepoEnrollmentsExt

from oarepo_communities import OARepoCommunities
from oarepo_communities.api import OARepoCommunity
from oarepo_communities.handlers import CommunityHandler
from oarepo_communities.permissions import RequestApproval, Approve, RevertApprove, Publish, Unpublish, RequestChanges
from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.search import CommunitySearch
from tests.api.helpers import gen_rest_endpoint, make_sample_record, LiteEntryPoint

logging.basicConfig()
logging.getLogger('elasticsearch').setLevel(logging.DEBUG)


@pytest.fixture(scope='module')
def create_app():
    return create_api


@pytest.fixture(scope='module')
def app_config(app_config):
    app_config = dict(
        TESTING=True,
        APPLICATION_ROOT='/',
        WTF_CSRF_ENABLED=False,
        CACHE_TYPE='simple',
        SERVER_NAME='localhost',
        DEBUG=False,
        PIDSTORE_RECID_FIELD='id',
        EMAIL_BACKEND='flask_email.backends.locmem.Mail',
        SECRET_KEY='TEST',
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite://'),
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
        APP_ALLOWED_HOSTS=['localhost'],
        USERPROFILES_EXTEND_SECURITY_FORMS=True,
        RATELIMIT_ENABLED=False,
        RECORDS_REST_ENDPOINTS={
            'recid': gen_rest_endpoint('recid',
                                       CommunitySearch,
                                       'tests.api.helpers.TestRecord',
                                       '<community_id>/records-anonymous',
                                       custom_read_permission_factory=allow_all)
        }
    )
    app_config.pop('RATELIMIT_STORAGE_URL', None)
    return app_config


@pytest.fixture(scope='module')
def app(base_app):
    """Flask application fixture."""
    OARepoEnrollmentsExt(base_app)
    OARepoCommunities(base_app)

    # Register blueprints here
    # base_app.register_blueprint(create_blueprint_from_app(base_app))
    return base_app


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
        'A': {
            'members_id': str(uuid.uuid4()),
            'curators_id': str(uuid.uuid4()),
            'publishers_id': str(uuid.uuid4()),
        },
        'B': {
            'members_id': str(uuid.uuid4()),
            'curators_id': str(uuid.uuid4()),
            'publishers_id': str(uuid.uuid4()),
        }
    }


@pytest.fixture
def community(db):
    """Community fixture."""
    comid = 'comtest'
    community = OARepoCommunity.create(
        {'description': 'Community description'},
        title='Title',
        id_=comid)
    db.session.commit()
    yield comid, community


@pytest.fixture()
def sample_records(app, db, es_clear):
    try:
        current_search.client.indices.delete('records-record-v1.0.0')
    except:
        pass
    if 'records-record-v1.0.0' not in current_search.mappings:
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
            make_sample_record(db, 'Test 6 in community B', 'B', 'published', ['C']),
        ],
        'comtest': [
            make_sample_record(db, 'Test 4 in community comid', 'comid'),
        ]
    }
    current_search.flush_and_refresh('records-record-v1.0.0')
    return records


@pytest.yield_fixture()
def permissions(db, community, sample_records):
    """Permission for users."""
    users = {None: None}
    user_roles = ['author', 'curator', 'publisher', 'member']
    community_roles = {r.name.split(':')[-1]: r for r in community[1].roles}

    for role in user_roles:
        users[role] = create_test_user(
            email='{0}@invenio-software.org'.format(role),
            password='pass1',
            active=True
        )
        if role == 'author':
            current_datastore.add_role_to_user(users[role], community_roles['member'])
        else:
            current_datastore.add_role_to_user(users[role], community_roles[role])

    perms = [
        (RequestApproval, ['author']),
        (Approve, ['curator']),
        (RequestChanges, ['curator']),
        (RevertApprove, ['curator', 'publisher']),
        (Publish, ['publisher']),
        (Unpublish, ['publisher'])
    ]

    for perm, roles in perms:
        for r in roles:
            if r == 'author':
                db.session.add(ActionUsers.allow(
                    action=perm(community[1].id),
                    user=users[r]))
            else:
                role_name = current_oarepo_communities.role_name_factory(community[1], r)['name']
                role = current_datastore.find_role(role_name)
                db.session.add(ActionRoles.allow(perm(community[1].id), role=role))

    db.session.commit()

    yield users
