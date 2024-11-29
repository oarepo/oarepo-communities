from invenio_communities.generators import CommunityRoleNeed

from oarepo_communities.services.permissions.generators import CommunityMembers


def test_community_members_needs(app, db, sample_record_with_community_data, communities):
    members = CommunityMembers()
    assert set(members.needs(data=sample_record_with_community_data)) == {
        CommunityRoleNeed(str(communities['aaa'].id), 'owner'),
        CommunityRoleNeed(str(communities['bbb'].id), 'owner'),
        CommunityRoleNeed(str(communities['aaa'].id), 'manager'),
        CommunityRoleNeed(str(communities['bbb'].id), 'manager'),
        CommunityRoleNeed(str(communities['aaa'].id), 'curator'),
        CommunityRoleNeed(str(communities['bbb'].id), 'curator'),
        CommunityRoleNeed(str(communities['aaa'].id), 'reader'),
        CommunityRoleNeed(str(communities['bbb'].id), 'reader'),
    }

def test_community_members_excludes(app, db, sample_record_with_community_data, communities):
    members = CommunityMembers()
    assert not set(members.excludes(data=sample_record_with_community_data))

def test_community_members_query_filter(app, db, sample_record_with_community_data, communities, community_owner, as_comparable_dict):
    members = CommunityMembers()
    assert as_comparable_dict(members.query_filter(identity=community_owner.identity).to_dict()) == as_comparable_dict({
        'terms': {
           'parent.communities.ids': [
               str(communities['aaa'].id),
               str(communities['bbb'].id)
           ]
        }
    })