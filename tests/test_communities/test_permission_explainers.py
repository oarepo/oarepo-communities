#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for oarepo_communities.services.permissions.explainers."""

from __future__ import annotations

from invenio_records_permissions import RecordPermissionPolicy
from oarepo_runtime.services.permission_explainer import format_explanation

from oarepo_communities.services.permissions.explainers import (
    CommunityRolePermissionExplainer,
    InAnyCommunityPermissionExplainer,
)
from oarepo_communities.services.permissions.generators import (
    CommunityRole,
    DefaultCommunityRole,
    InAnyCommunity,
)


class SampleCommunityPolicy(RecordPermissionPolicy):
    """Permission policy exercising the community explainers."""

    can_owner = (InAnyCommunity(DefaultCommunityRole("owner")),)
    can_default_owner = (DefaultCommunityRole("owner"),)
    can_role = (CommunityRole("curator"),)


def test_in_any_community_explainer_lists_each_community(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    community_2 = community_get_or_create_in_default_workflow(community_owner, "comm2")

    policy = SampleCommunityPolicy("owner")
    generator = SampleCommunityPolicy.can_owner[0]

    result = InAnyCommunityPermissionExplainer(policy, generator).explain(community_owner.identity)

    # community_owner owns both communities, so the aggregate generator allows access
    assert result[0].startswith("✅ InAnyCommunity")

    formatted = format_explanation(result)
    assert f"community: {community_1.slug}" in formatted
    assert f"community: {community_2.slug}" in formatted
    # nested per-community explanation delegates to the wrapped DefaultCommunityRole generator
    assert formatted.count("✅ DefaultCommunityRole") == 2


def test_in_any_community_explainer_denies_for_non_member(
    community_owner,
    users,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_get_or_create_in_default_workflow(community_owner, "comm1")
    outsider = users[0]

    policy = SampleCommunityPolicy("owner")
    generator = SampleCommunityPolicy.can_owner[0]

    result = InAnyCommunityPermissionExplainer(policy, generator).explain(outsider.identity)

    assert result[0].startswith("❌ InAnyCommunity")
    formatted = format_explanation(result)
    assert "❌ DefaultCommunityRole" in formatted


def test_community_role_explainer_prints_roles_for_default_community_role(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")

    policy = SampleCommunityPolicy("default_owner", community=community_1)
    generator = SampleCommunityPolicy.can_default_owner[0]

    result = CommunityRolePermissionExplainer(policy, generator).explain(community_owner.identity)

    assert result[0].startswith("✅ DefaultCommunityRole")
    assert result[-1] == "  - roles: ['owner']"


def test_community_role_explainer_prints_roles_for_community_role(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")

    policy = SampleCommunityPolicy("role", community=community_1)
    generator = SampleCommunityPolicy.can_role[0]

    result = CommunityRolePermissionExplainer(policy, generator).explain(community_owner.identity)

    # community_owner has the "owner" role, not "curator", so access is denied ...
    assert result[0].startswith("❌ CommunityRole")
    # ... but the configured roles are still reported
    assert result[-1] == "  - roles: ['curator']"
