import sys

import click
import yaml
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_communities.communities.records.api import Community
from invenio_records_resources.proxies import current_service_registry
from oarepo_runtime.cli.base import oarepo


@oarepo.group()
def communities():
    """OARepo communities commands."""


@communities.command(name="create")
@click.argument("slug")
@click.argument("title")
@click.option("--public/--private", default=True)
@with_appcontext
def create_community(slug, title, public):
    community_service = current_service_registry.get("communities")
    community_service.create(
        system_identity,
        {
            "slug": slug,
            "metadata": {"title": title},
            "access": {"visibility": "public" if public else "restricted"},
        },
    )


@communities.command(name="list")
@with_appcontext
def list_communities():
    community_service = current_service_registry.get("communities")
    yaml.dump_all(
        community_service.read_all(
            system_identity, fields=["id", "slug", "metadata", "access", "featured"]
        ),
        sys.stdout,
    )


@communities.group(name="members")
def community_members():
    """Community members commands."""


@community_members.command(name="add")
@click.argument("community")
@click.argument("email")
@click.argument("role", default="member")
@with_appcontext
def add_community_member(community, email, role):
    # convert community slug to id
    community_id = Community.pid.resolve(community).id
    # convert user email to id
    user_id = User.query.filter_by(email=email).first().id

    members_service = current_service_registry.get("members")
    members_service.add(
        system_identity,
        community_id,
        {
            "members": [
                {
                    "type": "user",
                    "id": str(user_id),
                }
            ],
            "role": role,
        },
    )


@community_members.command(name="remove")
@click.argument("community")
@click.argument("email")
@with_appcontext
def add_community_member(community, email):
    # convert community slug to id
    community_id = Community.pid.resolve(community).id
    # convert user email to id
    user_id = User.query.filter_by(email=email).first().id

    members_service = current_service_registry.get("members")
    members_service.delete(
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
