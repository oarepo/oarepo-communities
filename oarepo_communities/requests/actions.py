from invenio_records_resources.services.uow import RecordCommitOp
from invenio_requests.customizations import actions
from oarepo_requests.utils import get_matching_service_for_record

from oarepo_communities.proxies import current_oarepo_communities


class ChangeRecordStatusMixin:
    def _try_state_change(self, action, state, request_states, topic, uow):
        if self.action == action and state in request_states:
            topic.status = request_states[state]
            service = get_matching_service_for_record(topic)
            uow.register(RecordCommitOp(topic, indexer=service.indexer))

    def execute(self, identity, uow, *args, **kwargs):
        super().execute(identity, uow, *args, **kwargs)
        request = self.request
        topic = request.topic.resolve()
        request_type = request.type
        workflow = getattr(topic.parent, "workflow", None)
        status = topic.status
        try:
            request_states = current_oarepo_communities.record_workflow[workflow][
                status
            ]["requests"][request_type.type_id]["states"]
        except KeyError:
            return
        self._try_state_change("submit", "pending", request_states, topic, uow)
        self._try_state_change("accept", "accept", request_states, topic, uow)
        self._try_state_change("decline", "decline", request_states, topic, uow)


class StatusChangingSubmitAction(ChangeRecordStatusMixin, actions.SubmitAction):
    action = "submit"


class StatusChangingDeclineAction(ChangeRecordStatusMixin, actions.SubmitAction):
    action = "decline"
