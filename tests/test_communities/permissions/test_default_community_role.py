from invenio_communities.generators import CommunityRoleNeed

from oarepo_communities.services.permissions.generators import CommunityRole, DefaultCommunityRole


def test_default_community_role_needs(app, db, sample_record_with_community_data, communities):
    role = DefaultCommunityRole("owner")
    assert set(role.needs(data=sample_record_with_community_data)) == {
        CommunityRoleNeed(str(communities['aaa'].id), 'owner'),
    }

def test_default_community_role_excludes(app, db, sample_record_with_community_data, communities):
    role = DefaultCommunityRole("owner")
    assert not set(role.excludes(data=sample_record_with_community_data))

def test_default_community_role_query_filter(app, db, sample_record_with_community_data, communities, community_owner, as_comparable_dict):
    role = DefaultCommunityRole("owner")
    assert as_comparable_dict(role.query_filter(identity=community_owner.identity).to_dict()) == as_comparable_dict({
        'terms': {
           'parent.communities.default': [
               str(communities['aaa'].id),
               str(communities['bbb'].id)
           ]
        }
    })