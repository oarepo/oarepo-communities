# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import click
from click import UUID
from flask.cli import with_appcontext
from invenio_accounts.models import User
from invenio_app.factory import create_api
from sqlalchemy.exc import IntegrityError

from oarepo_communities.api import OARepoCommunity
from invenio_db import db


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('create')
@click.argument('community-id')  # Community PID that will be part of community URLs
@click.argument('members', type=UUID)  # help='Role name of the users that should be all members of the community')
@click.argument('curators', type=UUID)  # help='Role name of the users that should be the curators in the community')
@click.argument('publishers', type=UUID)  # help='Role name of the users that should have publishing rights')
@click.option('--description', help='Community description')
@click.option('--policy', help='Curation policy')
@click.option('--title', help='Community title')
@click.option('--logo-path', help='Path to the community logo file')
@with_appcontext
def create(community_id, members, curators, publishers, description, policy, title, logo_path):
    comm_data = {
        "curation_policy": policy,
        "id": community_id,
        "title": title,
        "description": description,
        # TODO: "logo": "data/community-logos/ecfunded.jpg"
    }
    api = create_api()
    with api.app_context():
        try:
            comm = OARepoCommunity.create(comm_data,
                                   id_=community_id,
                                   members_id=members, curators_id=curators, publishers_id=publishers)

        except IntegrityError:
            click.secho(f'Community {community_id} already exists', fg='red')
            exit(1)

        db.session.commit()
        click.secho('Created community: ', comm, fg='green')
