# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import click
from invenio_accounts.models import User
from invenio_communities.api import Community as CommunityRecord
from invenio_communities.members.api import CommunityMember
from invenio_db import db


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('create')
@click.argument('community-id')  # Community PID that will be part of community URLs
@click.option('--members', help='Role name of the users that should be all members of the community')
@click.option('--curators', help='Role name of the users that should be the curators in the community')
@click.option('--publishers', help='Role name of the users that should be the publishers in the community')
@click.option('--owner', help='User that should be the owner of the community')
@click.option('--description', help='Community description')
@click.option('--policy', help='Curation policy')
@click.option('--title', help='Community title')
@click.option('--logo-path', help='Path to the community logo file')
def create(community_id, members, curators, publishers, owner, description, policy, title, logo_path):
    owner_id = User.query.filter_by(email=owner).one().id
    comm_data = {
        "curation_policy": policy,
        "id": community_id,
        "title": title,
        "owner_email": owner,
        # TODO: "logo": "data/community-logos/ecfunded.jpg"
    }
    c = CommunityRecord.create(community_id, owner_id, **comm_data)
    # TODO: support community logo
    # if logo_path:
    #     logo = file_stream(logo_path)
    #     ext = save_and_validate_logo(logo, logo.name, community_id)
    #     c.logo_ext = ext
    db.session.commit()
    CommunityMember.create()

