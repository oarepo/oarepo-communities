import inspect
from itertools import chain

from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl

from ..proxies import current_oarepo_communities
from .identity import request_active



def _needs_from_workflow(
    access_path, access_key, record=None, community_id=None, **kwargs
):
    try:
        path = dict_lookup(current_oarepo_communities.record_workflow, access_path)
        generators = dict_lookup(path, access_key)
    except KeyError:
        return []
    needs = [
        g.needs(
            record=record,
            community_id=community_id,
            **kwargs,
        )
        for g in generators
    ]
    return set(chain.from_iterable(needs))

def needs_from_workflow(
    workflow, status, request_type, access_key, topic=None, community_id=None, **kwargs
):
    access_path = f"{workflow}.{status}.requests.{request_type}"
    return _needs_from_workflow(access_path, access_key, topic, community_id, **kwargs)


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

    def needs(self, topic=None, request_type=None, **kwargs):
        if (
            not topic or not request_type
        ):  # invenio requests service does not have a way to input these
            if "request" in kwargs:
                request = kwargs["request"]
                topic = request.topic.resolve()
                request_type = request.type
            else:
                ret = self._get_topic_and_request_type_from_stack()
                if not ret:
                    return []
                request_type = ret[0]
                topic = ret[1]
        workflow = getattr(topic.parent, "workflow", None)
        status = topic.status

        access_path = f"{workflow}.{status}.requests.{request_type.type_id}"
        return _needs_from_workflow(access_path, self.access_key, topic, str(topic.parent.communities.default.id), **kwargs)

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

        access_path = f"{workflow}.{status}.roles"
        return _needs_from_workflow(access_path, self.access_key, record, str(record.parent.communities.default.id),
                                    **kwargs)


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
