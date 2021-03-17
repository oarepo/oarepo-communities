# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import url_for
from invenio_access import ActionRoles
from invenio_accounts.models import Role, User
from invenio_accounts.proxies import current_datastore

from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, STATE_PUBLISHED


def test_links_from_search(app, client, es, sample_records):
    resp = client.get('https://localhost/C/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 1  # 1 published record having secondary community C assigned
    assert resp.json['hits']['hits'][0]['links']['self'] == 'https://localhost/B/6'


def test_records_get(db, app, community, client, users, es, sample_records, test_blueprint):
    # Non-community members cannot read on primary neither secondary community
    resp = client.get('https://localhost/B/7')
    assert resp.status_code == 401

    resp = client.get('https://localhost/comtest/7')
    assert resp.status_code == 401

    role = Role.query.all()[0]
    user = User.query.all()[0]
    community[1].allow_action(role, COMMUNITY_READ)
    db.session.add(ActionRoles(action=COMMUNITY_READ, argument='B', role=role))
    db.session.commit()
    current_datastore.add_role_to_user(user, role)

    with app.test_client() as client:
        resp = client.get(url_for(
            '_tests.test_login_{}'.format(user.id), _scheme='https', _external=True))
        assert resp.status_code == 200

        # Record should be accessible in the primary community collection
        resp = client.get('https://localhost/comtest/7')
        assert resp.status_code == 200
        assert resp.json['links']['self'] == 'https://localhost/comtest/7'

        # Record should also be readable in the secondary community collection
        resp = client.get('https://localhost/B/7')
        assert resp.status_code == 200
        assert resp.json['links']['self'] == 'https://localhost/comtest/7'

        # Record get should return 404 on any other community
        resp = client.get('https://localhost/C/7')
        assert resp.status_code == 404


def test_record_create(db, app, community, client, users, es, test_blueprint):
    # Non-community members cannot create records in a community.
    recdata = {
        'title': 'Test record',
        '_primary_community': community[0],
        'state': '',
        '_communities': ['B'],
        'access': {
            'owned_by': [1]
        }
    }

    resp = client.post('https://localhost/comtest/', json=recdata)
    assert resp.status_code == 401

    role = Role.query.all()[0]
    user = User.query.all()[0]
    community[1].allow_action(role, COMMUNITY_READ)
    community[1].allow_action(role, COMMUNITY_CREATE)
    current_datastore.add_role_to_user(user, role)

    with app.test_client() as client:
        resp = client.get(url_for(
            '_tests.test_login_{}'.format(user.id), _external=True))
        assert resp.status_code == 200

        # Create with correct primary community  data succeeds
        resp = client.post('https://localhost/comtest/', json=recdata)
        assert resp.status_code == 201


def test_anonymous_permissions(sample_records, community, client):
    """Test anonymous rest permissions."""
    for state, record in sample_records['comtest'][1].items():
        if state != STATE_PUBLISHED:
            resp = client.get(f'https://localhost/comtest/{record.pid.pid_value}')
            assert resp.status_code == 401
        else:
            resp = client.get(f'https://localhost/comtest/{record.pid.pid_value}')
            assert resp.status_code == 200

        # No create
        resp = client.post(f'https://localhost/comtest/', json=record.record.dumps())
        assert resp.status_code == 401

        # No update
        resp = client.put(f'https://localhost/comtest/{record.pid.pid_value}',
                          json={'op': 'replace', 'path': '/title', 'value': 'qux'})
        assert resp.status_code == 401

        # No delete
        resp = client.delete(f'https://localhost/comtest/{record.pid.pid_value}')
        assert resp.status_code == 401
