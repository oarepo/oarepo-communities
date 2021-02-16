# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import os

from click.testing import CliRunner
from flask.cli import ScriptInfo
from invenio_accounts.models import Role

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.cli import communities as cmd


def test_cli_community_create(app, db, community_ext_groups):
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI',
                                                      'sqlite://')

    # Test community creation.
    with runner.isolated_filesystem():
        result = runner.invoke(cmd, ['create',
                                     'cli-test-community',
                                     '--description', 'community desc',
                                     '--title', 'Test Community',
                                     *community_ext_groups['A'].values()],
                               env={'INVENIO_SQLALCHEMY_DATABASE_URI':
                                        os.getenv('SQLALCHEMY_DATABASE_URI',
                                                  'sqlite://')},
                               obj=script_info)
        assert 0 == result.exit_code

        comm = OARepoCommunity.get_community('cli-test-community')
        assert comm is not None
        assert comm.json['title'] == 'Test Community'
        assert comm.json['description'] == 'community desc'

        rols = Role.query.all()
        assert len(rols) == 3
        assert {comm.members_id, comm.curators_id, comm.publishers_id} == {
            r.id for r in rols
        }
