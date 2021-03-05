# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import os

from click.testing import CliRunner
from flask import g
from flask.cli import ScriptInfo
from flask_security import login_user
from invenio_access import action_factory, Permission, ParameterizedActionNeed, ActionRoles
from invenio_access.utils import get_identity
from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.cli import communities as cmd
from oarepo_communities.constants import COMMUNITY_READ


def test_cli_community_create(cli_runner, db):
    # Test community creation.
    result = cli_runner(cmd, ['create',
                                 'cli-test-community',
                                 'Test Community',
                                 '--description', 'community desc',
                                 '--ctype', 'wgroup'],
                        )
    assert 0 == result.exit_code

    comm = OARepoCommunity.get_community('cli-test-community')
    assert comm is not None
    assert comm.title == 'Test Community'
    assert comm.type == 'wgroup'
    assert comm.json['description'] == 'community desc'

    rols = Role.query.all()
    assert len(rols) == 3
    assert set([r.name for r in rols]) == {'community:cli-test-community:member',
                                           'community:cli-test-community:curator',
                                           'community:cli-test-community:publisher'}


def test_cli_action_allow(app, community, authenticated_user, db):
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI',
                                                      'sqlite://')
    role = community[1].roles[0]
    current_datastore.add_role_to_user(authenticated_user, role)

    read_need = action_factory(COMMUNITY_READ, parameter=True)
    login_user(authenticated_user)
    assert not Permission(read_need(community[0])).allows(g.identity)

    # Test community creation.
    with runner.isolated_filesystem():
        result = runner.invoke(cmd, ['actions',
                                     'allow',
                                     community[0],
                                     role.name.split(':')[-1],
                                     COMMUNITY_READ[len('community-'):]],
                               env={'INVENIO_SQLALCHEMY_DATABASE_URI':
                                        os.getenv('SQLALCHEMY_DATABASE_URI',
                                                  'sqlite://')},
                               obj=script_info)
        assert 0 == result.exit_code
        assert Permission(ParameterizedActionNeed(COMMUNITY_READ, community[0])).allows(g.identity)


def test_cli_action_deny(app, community, authenticated_user, db):
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI',
                                                      'sqlite://')

    role = community[1].roles[0]
    current_datastore.add_role_to_user(authenticated_user, role)

    login_user(authenticated_user)

    db.session.add(ActionRoles(action=COMMUNITY_READ, argument=community[0], role=role))

    assert Permission(ParameterizedActionNeed(COMMUNITY_READ, community[0])).allows(g.identity)

    # Test community creation.
    with runner.isolated_filesystem():
        result = runner.invoke(cmd, ['actions',
                                     'deny',
                                     community[0],
                                     role.name.split(':')[-1],
                                     COMMUNITY_READ[len('community-'):]],
                               env={'INVENIO_SQLALCHEMY_DATABASE_URI':
                                        os.getenv('SQLALCHEMY_DATABASE_URI',
                                                  'sqlite://')},
                               obj=script_info)
        assert 0 == result.exit_code
        assert not Permission(ParameterizedActionNeed(COMMUNITY_READ, community[0])).allows(g.identity)

