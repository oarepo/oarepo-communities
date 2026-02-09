from invenio_rdm_records.requests.community_submission import CommunitySubmission as InvenioCommunitySubmission
from oarepo_requests.types.ref_types import ModelRefTypes
from invenio_rdm_records.requests.community_submission import AcceptAction as InvenioAcceptAction
from oarepo_requests.services.permissions.identity import request_active

class AcceptAction(InvenioAcceptAction):
    # publishing in workflows is permitted for request
    def execute(self, identity, uow, **kwargs):
        identity.provides.add(request_active)
        try:
            super().execute(identity, uow, **kwargs)
        finally:
            identity.provides.remove(request_active)

class CommunitySubmission(InvenioCommunitySubmission):
    # type_id = "community_submission" won't work without ui change
    allowed_topic_ref_types = ModelRefTypes()

    available_actions = {**InvenioCommunitySubmission.available_actions, "accept": AcceptAction}
