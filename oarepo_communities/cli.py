# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import click
from flask.cli import with_appcontext
from invenio_db import db
from oarepo_micro_api.cli import with_api
from sqlalchemy.exc import IntegrityError

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.errors import OARepoCommunityCreateError
from oarepo_communities.models import OAREPO_COMMUNITIES_TYPES


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('create')
@with_appcontext
@with_api
@click.argument('community-id')  # Community PID that will be part of community URLs
@click.argument('title')
@click.option('--description', help='Community description')
@click.option('--policy', help='Curation policy')
@click.option('--logo-path', help='Path to the community logo file')
@click.option('--ctype', help='Type of a community', default='other')
def create(community_id, description, policy, title, ctype, logo_path):
    topts = [t[0] for t in OAREPO_COMMUNITIES_TYPES]
    if ctype not in topts:
        click.secho(f'Invalid Community type {ctype}. Choices: {topts}', fg='red')
        exit(3)

    comm_data = {
        "curation_policy": policy,
        "id": community_id,
        "description": description,
        # TODO: "logo": "data/community-logos/ecfunded.jpg"
    }
    try:
        comm = OARepoCommunity.create(
            comm_data,
            id_=community_id,
            title=title,
            ctype=ctype
        )
    except IntegrityError:
        click.secho(f'Community {community_id} already exists', fg='red')
        exit(4)
    except OARepoCommunityCreateError as e:
        click.secho(e, fg='red')
        exit(5)

    db.session.commit()
    click.secho(f'Created community: {comm}', fg='green')
