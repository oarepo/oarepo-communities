# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


"""Basic record to community integration test."""


from .mock_module.api import MockRecord


def test_community_integration(db, community, app, full_record, extra_entry_points):
    """Basic smoke test for communities integration."""
    record = MockRecord.create(full_record)
    record.commit()
    db.session.commit()
    print(community)
    record.communities.add(community, default=True)
    record.commit()
    assert record.dumps()['communities'] == {
        'default': str(community.id),
        'ids': [str(community.id)],
    }
    db.session.commit()
