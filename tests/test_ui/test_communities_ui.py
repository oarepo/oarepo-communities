#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for oarepo-communities UI."""

from __future__ import annotations

from flask import url_for
from invenio_access.permissions import system_identity


def test_communities_ui(community_service, logged_client, users, fake_manifest, community_type_type):
    """Test community ui is registered."""
    from invenio_communities.members.records.api import Member

    test_community = community_service.create(
        system_identity,
        {
            "slug": "test-community",
            "metadata": {"title": "Test Community"},
            "access": {"visibility": "public"},
        },
    ).to_dict()
    pid_value = test_community["slug"]
    community_id = test_community["id"]

    # Add user as owner so they can access settings/members/invitations pages
    community_service.members.add(
        system_identity,
        community_id,
        data={"members": [{"type": "user", "id": str(users[0].id)}], "role": "owner"},
    )
    Member.index.refresh()

    creator_client = logged_client(users[0])

    # Test frontpage
    frontpage_url = url_for("invenio_communities.communities_frontpage")
    with creator_client.get(frontpage_url) as response:
        assert response.status_code == 200

    # Test settings page
    settings_url = url_for("invenio_communities.communities_settings", pid_value=pid_value)
    with creator_client.get(settings_url) as response:
        assert response.status_code == 200

    # Test members page
    members_url = url_for("invenio_communities.members", pid_value=pid_value)
    with creator_client.get(members_url) as response:
        assert response.status_code == 200

    # Test invitations page
    invitations_url = url_for("invenio_communities.invitations", pid_value=pid_value)
    with creator_client.get(invitations_url) as response:
        assert response.status_code == 200
    communities_records_url = url_for("invenio_app_rdm_communities.communities_detail", pid_value=pid_value)
    with creator_client.get(communities_records_url) as response:
        assert response.status_code == 200
