# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from itertools import groupby
from operator import attrgetter

import click
import sqlalchemy
from flask.cli import with_appcontext
from invenio_access import ActionRoles, any_user
from invenio_db import db
from sqlalchemy.exc import IntegrityError

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.errors import OARepoCommunityCreateError
from oarepo_communities.models import OAREPO_COMMUNITIES_TYPES, OARepoCommunityModel
from oarepo_communities.permissions import community_record_owner
from oarepo_communities.proxies import current_oarepo_communities


@click.group()
def communities():
    """Management commands for OARepo Communities."""


@communities.command('list')
@with_appcontext
def list_communities():
    """List all OARepo communities."""
    comm = OARepoCommunityModel.query.all()
    for c in comm:
        click.secho(f'- {c.id} - ', fg='yellow', nl=False)
        click.secho(f'{c.title} ', fg='green', nl=False)
        click.secho(c.json.get('description', ''))


@communities.command('create')
@with_appcontext
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


def _validate_role(community, role):
    role = OARepoCommunity.get_role(community, role)
    if not role:
        click.secho(f'Role {role} does not exist', fg='red')
        exit(4)
    return role


def _validate_community(community):
    _community = None
    try:
        _community = OARepoCommunity.get_community(community)
    except sqlalchemy.orm.exc.NoResultFound:
        click.secho(f'Community {community} does not exist', fg='red')
        exit(3)
    return _community


def _validate_actions(actions):
    if not actions:
        exit(0)

    def _action_valid(action):
        if f'community-{action}' in current_oarepo_communities.allowed_actions:
            return True
        click.secho(f'Action {action} not allowed', fg='red')

    actions = [a for a in actions if _action_valid(a)]

    return actions


def _allow_actions(community, actions, role, system=False):
    with db.session.begin_nested():
        for action in actions:
            _action = f'community-{action}'
            ar = community.allow_action(role, _action, system)
            click.secho(f'Added role action: {ar.action} {ar.need}', fg='green')

    db.session.commit()


def _deny_actions(community, actions, role, system=False):
    with db.session.begin_nested():
        for action in actions:
            _action = f'community-{action}'
            click.secho(f'Removing role action: {_action}', fg='green')
            community.deny_action(role, _action, system)

    db.session.commit()


@community_actions.command('list')
@with_appcontext
@click.option('-c', '--community', help='List allowed and available actions in a community')
def list_actions(community=None):
    """List all available community actions."""
    click.secho('Available actions:', fg='green')
    for action in current_oarepo_communities.allowed_actions:
        _action = action[len('community-'):]
        click.secho(f'- {_action}')

    if community:
        community = _validate_community(community)
        click.secho('\nAvailable community roles:', fg='green')
        for role in community.roles:
            click.secho(f'- {role.name.split(":")[-1]}')

        click.secho('\nAllowed community actions:', fg='green')
        ars = ActionRoles.query \
            .filter_by(argument=community.id) \
            .order_by(ActionRoles.action).all()
        ars = [{k: list(g)} for k, g in groupby(ars, key=attrgetter('action'))]
        for ar in ars:
            for action, roles in ar.items():
                click.secho(f'- {action[len("community-"):]}: ', nl=False, fg='yellow')
                click.secho(', '.join([r.need.value.split(':')[-1] for r in roles]))


@community_actions.command('allow')
@with_appcontext
@click.argument('community')
@click.argument('role')
@click.argument('actions', nargs=-1)
def allow_actions(community, role, actions):
    """Allow actions to the given role."""
    actions = _validate_actions(actions)
    community = _validate_community(community)

    if role == 'any':
        # Allow actions for anonymous users
        _allow_actions(community, actions, any_user, system=True)
    elif role == 'author':
        # Allow actions for record owners
        _allow_actions(community, actions, community_record_owner, system=True)
    else:
        role = _validate_role(community, role)
        _allow_actions(community, actions, role)


@community_actions.command('deny')
@with_appcontext
@click.argument('community')
@click.argument('role')
@click.argument('actions', nargs=-1)
def deny_actions(community, role, actions):
    """Deny actions on the given role."""
    actions = _validate_actions(actions)
    community = _validate_community(community)

    if role == 'any':
        # Allow actions for anonymous users
        _deny_actions(community, actions, any_user, system=True)
    elif role == 'author':
        # Allow actions for record owners
        _deny_actions(community, actions, community_record_owner, system=True)
    else:
        role = _validate_role(community, role)
        _deny_actions(community, actions, role)

    db.session.commit()
