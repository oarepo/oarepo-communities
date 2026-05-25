#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_communities.generators import CommunityRoleNeed

from oarepo_communities.services.permissions.generators import (
    CommunityRole,
    PrimaryCommunityRole,
    TargetCommunityRole,
)


def test_community_role_needs(app, db, sample_record_with_community_data, communities):
    role = CommunityRole("owner")
    assert set(role.needs(data=sample_record_with_community_data)) == {
        CommunityRoleNeed(str(communities["aaa"].id), "owner"),
        CommunityRoleNeed(str(communities["bbb"].id), "owner"),
    }


def test_community_role_excludes(app, db, sample_record_with_community_data, communities):
    role = CommunityRole("owner")
    assert not set(role.excludes(data=sample_record_with_community_data))


def test_community_role_query_filter(
    app,
    db,
    sample_record_with_community_data,
    communities,
    community_owner,
    as_comparable_dict,
):
    role = CommunityRole("owner")
    assert as_comparable_dict(role.query_filter(identity=community_owner.identity).to_dict()) == as_comparable_dict(
        {
            "terms": {
                "parent.communities.ids": [
                    str(communities["aaa"].id),
                    str(communities["bbb"].id),
                ]
            }
        }
    )


def test_community_role_returns_empty_list_if_no_community_id(communities_model):
    role = CommunityRole("owner")
    primary_role = PrimaryCommunityRole("owner")

    assert role.needs(data={"parent": {}}) == []
    assert role.excludes(data={"parent": {}}) == []
    assert primary_role.needs(data={"parent": {}}) == []
    assert primary_role.excludes(data={"parent": {}}) == []

    assert role.needs(record=communities_model.Record({})) == []
    assert role.excludes(record=communities_model.Record({})) == []
    assert primary_role.needs(record=communities_model.Record({})) == []
    assert primary_role.excludes(record=communities_model.Record({})) == []


def test_reference_receivers_returns_empty_list_if_no_community_id(communities_model):
    primary_role = PrimaryCommunityRole("owner")
    target_role = TargetCommunityRole("owner")

    assert primary_role.reference_receivers(record=communities_model.Record({})) == []

    assert target_role.reference_receivers(data={}) == []
    assert target_role.reference_receivers(data={"payload": {}}) == []
    assert target_role.reference_receivers() == []
