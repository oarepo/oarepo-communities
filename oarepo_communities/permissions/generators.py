import inspect
from itertools import chain

from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl
from invenio_communities.generators import current_roles

from ..proxies import current_oarepo_communities
from .identity import request_active


class WorkflowRequestPermission(Generator):
    def __init__(self, access_key):
        super().__init__()
        self.access_key = access_key

    def _get_topic_and_request_type_from_stack(self):
        stack = inspect.stack(0)
        for frame_info in stack:
            locals = frame_info.frame.f_locals
            if (
                "request_type" in locals
                and locals["request_type"] is not None
                and "topic" in locals
                and locals["topic"] is not None
            ):
                return locals["request_type"], locals["topic"]
        return None

    def needs(self, record=None, request_type=None, **kwargs):
        if (
            not record or not request_type
        ):  # invenio requests service does not have a way to input these
            if "request" in kwargs:
                request = kwargs["request"]
                record = request.topic.resolve()
                request_type = request.type
            else:
                ret = self._get_topic_and_request_type_from_stack()
                if not ret:
                    return []
                request_type = ret[0]
                record = ret[1]
        workflow = getattr(record.parent, "workflow", None)
        status = record.status
        try:
            generators = current_oarepo_communities.record_workflow[workflow][status][
                "requests"
            ][request_type.type_id]
            generators = dict_lookup(generators, self.access_key)
        except KeyError:
            return []
        needs = [
            g.needs(
                record=record,
                community_id=str(record.parent.communities.default.id),
                **kwargs,
            )
            for g in generators
        ]
        return set(chain.from_iterable(needs))


class WorkflowPermission(Generator):
    def __init__(self, access_key):
        super().__init__()
        self.access_key = access_key

    def _get_status(self, record):
        return "draft" if getattr(record, "is_draft") else "published"

    def needs(self, record=None, **kwargs):
        if not record:  # invenio requests service does not have a way to input these
            return []
        workflow = getattr(record.parent, "workflow", None)
        status = self._get_status(record)
        try:
            generators = current_oarepo_communities.record_workflow[workflow][status][
                "roles"
            ]
            generators = dict_lookup(generators, self.access_key)
        except KeyError:
            return []
        needs = [
            g.needs(
                record=record,
                community_id=str(record.parent.communities.default.id),
                **kwargs,
            )
            for g in generators
        ]
        return set(chain.from_iterable(needs))


class RequestActive(Generator):
    """Allows system_process role."""

    def needs(self, **kwargs):
        """Enabling Needs."""
        return [request_active]

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as system process."""
        if request_active in identity.provides:
            return dsl.Q("match_all")
        else:
            return []


