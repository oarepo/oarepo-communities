# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""


from copy import deepcopy

import pytest
from flask import g
from flask_security import login_user, logout_user
from flask_security.utils import hash_password
from invenio_app.factory import create_api as _create_api
from invenio_communities.communities.records.api import Community

from oarepo_communities import config

from .records.mock_module.api import MockRecord


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        'invenio_db.model': [
            'mock_module = tests.records.mock_module.models',
        ],
        'invenio_jsonschemas.schemas': [
            'mocks = tests.records.mock_module.jsonschemas',
        ],
        'invenio_search.mappings': [
            'mocks = tests.records.mock_module.mappings',
        ]
    }


# TODO: this will be moved to pytest-invenio
class UserFixture_:
    """A user fixture for easy test user creation."""

    def __init__(self, email=None, password=None, active=True):
        """Constructor."""
        self._email = email
        self._active = active
        self._password = password
        self._identity = None
        self._user = None
        self._client = None

    #
    # Creation
    #
    def create(self, app, db):
        """Create the user."""
        with db.session.begin_nested():
            datastore = app.extensions["security"].datastore
            user = datastore.create_user(
                email=self.email,
                password=hash_password(self.password),
                active=self._active,
            )
        db.session.commit()
        self._user = user
        return self

    #
    # Properties
    #
    @property
    def user(self):
        """Get the user."""
        return self._user

    @property
    def id(self):
        """Get the user id as a string."""
        return str(self._user.id)

    @property
    def email(self):
        """Get the user."""
        return self._email

    @property
    def password(self):
        """Get the user."""
        return self._password

    #
    # App context helpers
    #
    @property
    def identity(self):
        """Create identity for the user."""
        if self._identity is None:
            # Simulate a full login
            assert login_user(self.user)
            self._identity = deepcopy(g.identity)
            # Clean up - we just want the identity object.
            logout_user()
        return self._identity

    @identity.deleter
    def identity(self):
        """Delete the user."""
        self._identity = None

    def app_login(self):
        """Create identity for the user."""
        assert login_user(self.user)

    def app_logout(self):
        """Create identity for the user."""
        assert logout_user()

    @identity.deleter
    def identity(self):
        """Delete the user."""
        self._identity = None

    #
    # Test client helpers
    #
    def login(self, client, logout_first=False):
        """Login the given client."""
        return self._login(client, '/', logout_first)

    def api_login(self, client, logout_first=False):
        """Login the given client."""
        return self._login(client, '/api/', logout_first)

    def logout(self, client):
        """Logout the given client."""
        return self._logout(client, '/')

    def api_logout(self, client):
        """Logout the given client."""
        return self._logout(client, '/api/')

    def _login(self, client, base_path, logout):
        """Login the given client."""
        if logout:
            self._logout(client, base_path)
        res = client.post(
            f'{base_path}login',
            data=dict(email=self.email, password=self.password),
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            follow_redirects=True,
        )
        assert res.status_code == 200
        return client

    def _logout(self, client, base_path):
        """Logout the client."""
        res = client.get(f'{base_path}logout')
        assert res.status_code < 400
        return client


@pytest.fixture(scope='session')
def UserFixture():
    """Class to create user fixtures from."""
    return UserFixture_


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture."""
    return {}


def _(x):
    """Identity function for string extraction."""
    return x


@pytest.fixture(scope='module')
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    For test purposes we need to enforce the configuration variables set in config.py.
    """
    supported_configurations = [
    ]

    for config_key in supported_configurations:
        app_config[config_key] = getattr(config, config_key, None)

    app_config['RECORDS_REFRESOLVER_CLS'] = \
        "invenio_records.resolver.InvenioRefResolver"
    app_config['RECORDS_REFRESOLVER_STORE'] = \
        "invenio_jsonschemas.proxies.current_refresolver_store"

    # Variable not used. We set it to silent warnings
    app_config['JSONSCHEMAS_HOST'] = 'not-used'

    # Enable communities
    app_config['COMMUNITIES_ENABLED'] = True

    return app_config


@pytest.fixture(scope='module')
def create_app(entry_points):
    """Create app fixture for API app."""
    return _create_api


def _es_create_indexes(current_search, current_search_client):
    """Create all registered Elasticsearch indexes."""
    to_create = [
        MockRecord.index._name,
        MockRecord.index._name
    ]
    # list to trigger iter
    list(current_search.create(ignore_existing=True, index_list=to_create))
    current_search_client.indices.refresh()


def _es_delete_indexes(current_search):
    """Delete all registered Elasticsearch indexes."""
    to_delete = [
        MockRecord.index._name,
        MockRecord.index._name
    ]
    list(current_search.delete(index_list=to_delete))


@pytest.fixture(scope='function')
def es_clear(es):
    """Clear Elasticsearch indices after test finishes (function scope).
    This fixture rollback any changes performed to the indexes during a test,
    in order to leave Elasticsearch in a clean state for the next test.
    """
    from invenio_search import current_search, current_search_client
    yield es
    _es_delete_indexes(current_search)
    _es_create_indexes(current_search, current_search_client)


@pytest.fixture(scope='function')
def full_record():
    """Full record data as dict coming from the external world."""
    return {
        "metadata": {
            "title": "Mock Record"
        }
    }


@pytest.fixture()
def minimal_community():
    """Data for a minimal community."""
    return {
        "id": "oarepo",
        "access": {
            "visibility": "public",
        },
        "metadata": {
            "title": "OARepo Repository",
            "type": "topic"
        }
    }


@pytest.fixture()
def owner(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="owner@oarepo.org",
        password="owner",
    )
    u.create(app, db)
    return u


@pytest.fixture(scope='function')
def community(app, owner, location, minimal_community):
    """Get the current RDM records service."""
    c = Community.create(
        minimal_community,
    )
    return c
