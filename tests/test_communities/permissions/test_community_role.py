from invenio_communities.generators import CommunityRoleNeed

from oarepo_communities.services.permissions.generators import CommunityRole


def test_community_role_needs(app, db, sample_record_with_community_data, communities):
    role = CommunityRole("owner")
    assert set(role.needs(data=sample_record_with_community_data)) == {
        CommunityRoleNeed(str(communities["aaa"].id), "owner"),
        CommunityRoleNeed(str(communities["bbb"].id), "owner"),
    }


def test_community_role_excludes(
    app, db, sample_record_with_community_data, communities
):
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
    assert as_comparable_dict(
        role.query_filter(identity=community_owner.identity).to_dict()
    ) == as_comparable_dict(
        {
            "terms": {
                "parent.communities.ids": [
                    str(communities["aaa"].id),
                    str(communities["bbb"].id),
                ]
            }
        }
    )
