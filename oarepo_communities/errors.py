from flask_babelex import lazy_gettext as _

class CommunityAlreadyIncludedException(Exception):
    """The record is already in the community."""

    description = "The record is already included in this community."


class CommunityNotIncludedException(Exception):
    """The record is already in the community."""

    description = "The record is not included in this community."


class PrimaryCommunityException(Exception):
    """The record is already in the community."""

    description = "Primary community can't be removed, can only be migrated to another."
