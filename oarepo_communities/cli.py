# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import click
from click import UUID
from flask import current_app
from flask.cli import with_appcontext
from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore
from oarepo_micro_api.cli import with_api
from sqlalchemy.exc import IntegrityError

from oarepo_communities.api import OARepoCommunity
from invenio_db import db


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('create')
@with_appcontext
@with_api
@click.argument('community-id')  # Community PID that will be part of community URLs
@click.argument('members', type=UUID)  # help='Group UUID of the users that should be all members of the community')
@click.argument('curators', type=UUID)  # help='Group UUID of the users that should be the curators in the community')
@click.argument('publishers', type=UUID)  # help='Group UUID of the users that should have publishing rights')
@click.option('--description', help='Community description')
@click.option('--policy', help='Curation policy')
@click.option('--title', help='Community title')
@click.option('--logo-path', help='Path to the community logo file')
@click.option('--ctype', help='Type of a community', default='other')
def create(community_id, members, curators, publishers, description, policy, title, ctype, logo_path):
    ctypes = current_app.config['OAREPO_COMMUNITIES_TYPES']
    if ctype not in ctypes.keys():
        click.secho(f'Invalid Community type {ctype}. Choices: {ctypes}', fg='red')
        exit(3)

    mem_role: Role = current_datastore.find_or_create_role(str(members))
    mem_role.description = 'member'
    current_datastore.put(mem_role)

    cur_role: Role = current_datastore.find_or_create_role(str(curators))
    cur_role.description = 'curator'
    current_datastore.put(cur_role)

    pub_role: Role = current_datastore.find_or_create_role(str(publishers))
    pub_role.description = 'publisher'
    current_datastore.put(pub_role)

    current_datastore.commit()

    comm_data = {
        "curation_policy": policy,
        "id": community_id,
        "title": title,
        "description": description,
        "type": ctype
        # TODO: "logo": "data/community-logos/ecfunded.jpg"
    }
    try:
        comm = OARepoCommunity.create(
            comm_data,
            id_=community_id,
            members_id=mem_role.id,
            curators_id=cur_role.id,
            publishers_id=pub_role.id
        )

    except IntegrityError:
        click.secho(f'Community {community_id} already exists', fg='red')
        exit(4)

    db.session.commit()
    click.secho(f'Created community: {comm}', fg='green')
