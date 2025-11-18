#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""CLI commands for communities."""

from __future__ import annotations

import sys

import click
import yaml
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_communities import current_communities
from invenio_communities.cli import communities
from invenio_communities.communities.records.api import Community


@communities.command(name="create")
@click.argument("slug")
@click.argument("title")
@click.option("--public/--private", default=True)
@with_appcontext
def create_community(slug: str, title: str, public: bool) -> None:
    """Create a community."""
    current_communities.service.create(
        system_identity,
        {
            "slug": slug,
            "metadata": {"title": title},
            "access": {"visibility": "public" if public else "restricted"},
        },
    )


@communities.command(name="list")
@with_appcontext
def list_communities() -> None:
    """List all communities."""
    yaml.dump_all(
        current_communities.service.read_all(system_identity, fields=["id", "slug", "metadata", "access", "featured"]),
        sys.stdout,
    )


@communities.group(name="members")
def community_members() -> None:
    """Community members commands."""


@community_members.command(name="add")
@click.argument("community")
@click.argument("email")
@click.argument("role", default="member")
@with_appcontext
def add_community_member(community: str, email: str, role: str) -> None:
    """Add a member to a community."""
    # convert community slug to id
    community_id = Community.pid.resolve(community).id
    if community_id is None:
        raise click.ClickException(f"Community with slug {community} not found")

    # convert user email to id
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException(f"User with email {email} not found")
    user_id = user.id

    current_communities.service.members.add(
        system_identity,
        str(community_id),
        {
            "members": [
                {
                    "type": "user",
                    "id": user_id,
                }
            ],
            "role": role,
        },
    )


@community_members.command(name="remove")
@click.argument("community")
@click.argument("email")
@with_appcontext
def remove_community_member(community: str, email: str) -> None:
    """Remove a member from a community."""
    # convert community slug to id
    community_id = Community.pid.resolve(community).id
    # convert user email to id
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException(f"User with email {email} not found")
    user_id = user.id

    current_communities.service.members.delete(
        system_identity,
        community_id,
        {
            "members": [
                {
                    "type": "user",
                    "id": str(user_id),
                }
            ]
        },
    )
