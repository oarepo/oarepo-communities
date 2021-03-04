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

from oarepo_communities.constants import COMMUNITY_READ


def test_links_from_search(app, client, es, sample_records):
    resp = client.get('https://localhost/C/records-anonymous/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 1  # 1 published record having secondary community C assigned
    assert resp.json['hits']['hits'][0]['links']['self'] == 'https://localhost/B/records-anonymous/6'


def test_links_from_get(db, app, community, client, users, es, sample_records, test_blueprint):
    # Non-community members cannot read
    resp = client.get('https://localhost/C/records-anonymous/6')
    assert resp.status_code == 401

    role = Role.query.all()[0]
    user = User.query.all()[0]
    assert community[1].id == community[0]
    community[1].allow_action(role, COMMUNITY_READ)
    current_datastore.add_role_to_user(user, role)

    with app.test_client() as client:
        resp = client.get(url_for(
            '_tests.test_login_{}'.format(user.id), _external=True))
        assert resp.status_code == 200

        resp = client.get('https://localhost/comtest/records-anonymous/7')
        assert resp.status_code == 200
        assert resp.json['links']['self'] == 'https://localhost/comtest/records-anonymous/7'
