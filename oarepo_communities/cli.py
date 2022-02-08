# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import re
import click
from click.exceptions import BadParameter
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from invenio_pidstore.errors import PIDAlreadyExists

# TODO: make reusable by other libs
def validate_slug (ctx, param, slug):
    if not isinstance(slug, str):
        return BadParameter('slug must be a string', ctx, param)

    if len(slug) < 3 or len(slug) > 63:
        raise BadParameter('slug must be between 3 and 63 characters in length', ctx, param)

    slug_pattern = re.compile('^[a-z][a-z0-9-]+[a-z0-9]$')
    if not slug_pattern.match(slug):
        raise BadParameter('slug is incorrectly formatted', ctx, param)

    return slug


@click.group()
def communities():
    """Invenio communities commands."""


@communities.command('create')
@click.option(
    '--id',
    prompt='Community ID',
    help='Short unique community ID (slug)',
    callback=validate_slug)
@click.option(
    '--title',
    prompt='Community name',
    type=str,
    help='Title name of a community')
@click.option(
    '--description',
    prompt='Description',
    type=str,
    help='Description of a community')
@click.option(
    '--type',
    prompt='Type',
    type=click.Choice(['organization', 'event', 'topic', 'project'], case_sensitive=True),
    default='organization',
    help='Type or topic of a community')
@with_appcontext
def create(id, title, description, type):
    """Create a new community."""
    service = current_communities.service
    owner_identity = system_identity
    data = {
        'access': {
            'visibility': 'public',
            # Record submission is always restricted to members only
            'record_policy': 'restricted',
            # Membership is managed by administrative mapping
            'member_policy': 'closed'
        },
        'id': id,
        'metadata': {
            'title': title,
            'description': description,
            'type': type,

        }
    }
    try:
        service.create(data=data, identity=system_identity)
    except PIDAlreadyExists:
        pass
