from invenio_requests.customizations import actions
from oarepo_requests.utils import get_matching_service_for_record

from oarepo_communities.proxies import current_oarepo_communities
from invenio_records_resources.services.uow import RecordCommitOp


class ChangeRecordStatusMixin:
    def _commit_topic(self, topic, uow):
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
            request_states = current_oarepo_communities.record_workflow[workflow][status][
                "requests"
            ][request_type.type_id]["states"]
        except KeyError:
            return
        if self.action == "submit" and "pending" in request_states:
            topic.status = request_states["pending"]
            self._commit_topic(topic, uow)
        if self.action == "accept" and "accept" in request_states:
            topic.status = request_states["accept"]
            self._commit_topic(topic, uow)
        if self.action == "decline" and "decline" in request_states:
            topic.status = request_states["decline"]
            self._commit_topic(topic, uow)

class PublishChangeRecordStatusMixin:
    def _commit_topic(self, topic, uow):
        service = get_matching_service_for_record(topic)
        uow.register(RecordCommitOp(topic, indexer=service.indexer))

    def execute(self, identity, uow, *args, **kwargs):
        record = super().execute(identity, uow, *args, **kwargs)
        request = self.request
        topic = request.topic.resolve()
        request_type = request.type
        workflow = getattr(topic.parent, "workflow", None)
        status = topic.status
        try:
            request_states = current_oarepo_communities.record_workflow[workflow][status][
                "requests"
            ][request_type.type_id]["states"]
        except KeyError:
            return
        if "accept" in request_states:
            record.status = request_states["accept"]
            self._commit_topic(record, uow)

class StatusChangingSubmitAction(ChangeRecordStatusMixin, actions.SubmitAction):
    action = "submit"

class StatusChangingDeclineAction(ChangeRecordStatusMixin, actions.SubmitAction):
    action = "decline"
