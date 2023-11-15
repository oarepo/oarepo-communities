def test_community_inclusion(sample_draft, community):
    assert sample_draft.parent.communities.default == community.id
    assert sample_draft.parent.communities.ids[0] == community.id
