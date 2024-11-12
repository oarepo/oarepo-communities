from flask_babelex import lazy_gettext as _
from marshmallow import ValidationError

class CommunityAlreadyIncludedException(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


class CommunityNotIncludedException(Exception):
    """The record is already in the community."""

    description = _("The record is not included in this community.")


class PrimaryCommunityException(Exception):
    """The record is already in the community."""

    description = _("Primary community can't be removed, can only be migrated to another.")


class MissingDefaultCommunityError(ValidationError):
    """"""
    description = _("Default community is not present in the input.")


class MissingCommunitiesError(ValidationError):
    """"""
    description = _("Communities are not present in the input.")

class CommunityAlreadyExists(Exception):
    """The record is already in the community."""

    description = _("The record is already included in this community.")


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


class OpenRequestAlreadyExists(Exception):
    """An open request already exists."""

    def __init__(self, request_id):
        """Initialize exception."""
        self.request_id = request_id

    @property
    def description(self):
        """Exception's description."""
        return _("There is already an open inclusion request for this community.")
