class CommunityAlreadyExists(Exception):
    """The record is already in the community."""

    description = "The record is already included in this community."


class RecordCommunityMissing(Exception):
    """Record does not belong to the community."""

    def __init__(self, record_id, community_id):
        """Initialise error."""
        self.record_id = record_id
        self.community_id = community_id

    @property
    def description(self):
        """Exception description."""
        return "The record {record_id} in not included in the community {community_id}.".format(
            record_id=self.record_id, community_id=self.community_id
        )
