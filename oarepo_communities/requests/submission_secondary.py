from oarepo_communities.requests.submission import CommunitySubmissionRequestType


class SecondaryCommunitySubmissionRequestType(CommunitySubmissionRequestType):
    """Review request for submitting a record to a community."""

    type_id = "secondary_community_submission"
    name = "Secondary_community_submission"

    needs_context = {"community_permission_name": "can_submit_secondary_community"}
    set_as_default = False