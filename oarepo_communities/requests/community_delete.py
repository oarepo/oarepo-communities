from oarepo_requests.types.delete_record import DeleteRecordRequestType


class CommunityDeleteRecordRequestType(DeleteRecordRequestType):
    allowed_receiver_ref_types = ["oarepo_community"]

    needs_context = {"community_permission_name": "can_delete_request"}
