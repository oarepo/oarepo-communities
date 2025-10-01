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

from oarepo_communities.services.permissions.generators import DefaultCommunityMembers


def test_community_members_needs(app, db, sample_record_with_community_data, communities):
    members = DefaultCommunityMembers()
    assert set(members.needs(data=sample_record_with_community_data)) == {
        CommunityRoleNeed(str(communities["aaa"].id), "owner"),
        CommunityRoleNeed(str(communities["aaa"].id), "manager"),
        CommunityRoleNeed(str(communities["aaa"].id), "curator"),
        CommunityRoleNeed(str(communities["aaa"].id), "reader"),
    }


def test_community_members_excludes(app, db, sample_record_with_community_data, communities):
    members = DefaultCommunityMembers()
    assert not set(members.excludes(data=sample_record_with_community_data))


def test_community_members_query_filter(
    app,
    db,
    sample_record_with_community_data,
    communities,
    community_owner,
    as_comparable_dict,
):
    members = DefaultCommunityMembers()
    assert as_comparable_dict(members.query_filter(identity=community_owner.identity).to_dict()) == as_comparable_dict(
        {
            "terms": {
                "parent.communities.default": [
                    str(communities["aaa"].id),
                    str(communities["bbb"].id),
                ]
            }
        }
    )
