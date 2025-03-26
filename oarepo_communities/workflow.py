from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_communities.communities.records.api import Community

from oarepo_communities.errors import MissingDefaultCommunityError, CommunityDoesntExistError
from oarepo_communities.utils import community_id_from_record
from invenio_pidstore.errors import PIDDoesNotExistError
if TYPE_CHECKING:
    from typing import Any


def community_default_workflow(**kwargs: Any) -> str | None:
    # optimization: if community metadata is passed, use it
    if "community_metadata" in kwargs:
        community_metadata = kwargs["community_metadata"]
        custom_fields = community_metadata.json.get("custom_fields", {})
        return custom_fields.get("workflow", "default")

    if "record" not in kwargs and "data" not in kwargs:  # nothing to get community from
        raise MissingDefaultCommunityError(
            "Can't get community when neither record nor input data are present."
        )

    if "record" in kwargs:
        community_id = community_id_from_record(kwargs["record"])
        if not community_id:
            raise MissingDefaultCommunityError("Failed to get community from record.")
    else:
        try:
            community_id = kwargs["data"]["parent"]["communities"]["default"]
        except KeyError:
            raise MissingDefaultCommunityError(
                "Failed to get community from input data."
            )

    # use pid resolve so that the community might be both slug or id
    try:
        community = Community.pid.resolve(community_id)
    except PIDDoesNotExistError:
        raise CommunityDoesntExistError(community_id)
    return community.custom_fields.get("workflow", "default")
