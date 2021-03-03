# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from itertools import groupby
from operator import attrgetter, itemgetter

import click
import sqlalchemy
from flask.cli import with_appcontext
from invenio_access import ActionRoles
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from oarepo_micro_api.cli import with_api
from sqlalchemy.exc import IntegrityError

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.errors import OARepoCommunityCreateError
from oarepo_communities.models import OAREPO_COMMUNITIES_TYPES, OARepoCommunityModel
from oarepo_communities.permissions import ALLOWED_ACTIONS
from oarepo_communities.proxies import current_oarepo_communities


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('list')
@with_appcontext
@with_api
def list_communities():
    """List all OARepo communities."""
    comm = OARepoCommunityModel.query.all()
    for c in comm:
        click.secho(f'- {c.id} - ', fg='yellow', nl=False)
        click.secho(f'{c.title} ', fg='green', nl=False)
        click.secho(c.json.get('description', ''))


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
    """Create a new community and associated community roles."""
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
    click.secho(f'Created community: {comm} with roles {[r.name for r in comm.roles]}', fg='green')


@communities.group('actions')
def community_actions():
    """Management commands for OARepo Communities actions."""


@community_actions.command('list')
@with_appcontext
@with_api
@click.option('-c', '--community', help='List allowed and available actions in a community')
def list_actions(community=None):
    """List all available community actions."""
    click.secho('Available actions:', fg='green')
    for action in ALLOWED_ACTIONS:
        _action = action[len('community-'):]
        click.secho(f'- {_action}')

    if community:
        _community = None
        try:
            _community = OARepoCommunity.get_community(community)
        except sqlalchemy.orm.exc.NoResultFound:
            click.secho(f'Community {community} does not exist', fg='red')

        if _community:
            click.secho('\nAvailable community roles:', fg='green')
            for role in _community.roles:
                click.secho(f'- {role.name}')

            click.secho('\nAllowed community actions:', fg='green')
            ars = ActionRoles.query\
                .filter_by(argument=_community.id)\
                .order_by(ActionRoles.action).all()
            ars = [{k: list(g)} for k, g in groupby(ars, key=attrgetter('action'))]
            for ar in ars:
                for action, roles in ar.items():
                    click.secho(f'- {action[len("community-"):]}: ', nl=False, fg='yellow')
                    click.secho(', '.join([r.need.value.split(':')[-1] for r in roles]))


def _validate_role_actions(role, actions):
    if not actions:
        exit(0)

    role = current_datastore.find_role(role)
    if not role:
        click.secho(f'Role {role} does not exist', fg='red')

    community = role.community.first()
    if not community:
        click.secho(f'Role {role} does not belong to any community', fg='red')
        exit(1)

    def _action_valid(action):
        if f'community-{action}' in ALLOWED_ACTIONS:
            return True
        click.secho(f'Action {action} not allowed', fg='red')

    actions = [a for a in actions if _action_valid(a)]

    return community, role, actions


@community_actions.command('allow')
@with_appcontext
@with_api
@click.argument('role')
@click.argument('actions', nargs=-1)
def allow_actions(role, actions):
    """Allow actions to the given role."""
    community, role, actions = _validate_role_actions(role, actions)

    with db.session.begin_nested():
        for action in actions:
            _action = f'community-{action}'

            if ActionRoles.query.filter_by(action=_action, argument=community.id, role_id=role.id).first():
                click.secho(f'Action {action} already allowed', fg='yellow')
                continue

            ar = ActionRoles(action=_action, argument=community.id, role=role)
            db.session.add(ar)
            click.secho(f'Adding role action: {ar.action} {ar.need}', fg='green')

    db.session.commit()


@community_actions.command('deny')
@with_appcontext
@with_api
@click.argument('role')
@click.argument('actions', nargs=-1)
def deny_actions(role, actions):
    """Deny actions on the given role."""
    community, role, actions = _validate_role_actions(role, actions)

    with db.session.begin_nested():
        for action in actions:
            _action = f'community-{action}'
            ars = ActionRoles.query.filter_by(action=_action, argument=community.id, role_id=role.id).all()
            for ar in ars:
                db.session.delete(ar)
                click.secho(f'Removing role action: {ar.action} {ar.need}', fg='green')

    db.session.commit()

