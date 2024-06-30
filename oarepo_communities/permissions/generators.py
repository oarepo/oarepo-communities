import inspect
from itertools import chain
from invenio_search.engine import dsl
from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import Generator

from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_roles

from ..proxies import current_oarepo_communities

"""
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
        status = topic.state

        request_type_id = (
            request_type.type_id if not isinstance(request_type, str) else request_type
        )
        access_path = f"{workflow}.{status}.requests.{request_type_id}"
        return _needs_from_workflow(
            access_path,
            self.access_key,
            community_id=str(topic.parent.communities.default.id),
            **kwargs,
        )


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
        return _needs_from_workflow(
            access_path,
            self.access_key,
            record,
            str(record.parent.communities.default.id),
            **kwargs,
        )
"""
from invenio_communities.generators import CommunityRoleNeed

def _get_community_id(record, community_id):
    if community_id is None:
        # todo this could be problem for invenio too, as they have the same
        # community_id = record.id and what is record depends on context - see the need for unified meaning of
        # permission kwargs
        # we shouldn't have to write complicated checks like this
        # this is hack that falls apart with different communityrecord class
        if isinstance(record, Community):
            community_id = record.id
        else:
            try:
                community_id = record.parent.communities.default.id
            except AttributeError:
                return None
    return community_id
class CommunityRole(Generator):

    def __init__(self, role):
        self.role = role

    def roles(self, **kwargs):
        return [self.role]

    def communities(self, identity):

        raise NotImplementedError

    def needs(self, record=None, community_id=None, **kwargs):

        community_id = _get_community_id(record, community_id)
        if not community_id:
            print("No community id provided.")
            return []

        assert community_id, "No community id provided."
        community_id = str(community_id)

        roles = self.roles(**kwargs)
        if roles:
            needs = [CommunityRoleNeed(community_id, role) for role in roles]
            return needs
        return []

    """
    def query_filter(self, identity=None, **kwargs):
        # Gives access to all community members.
        return dsl.Q("terms", **{"_id": self.communities(identity)})
    """

class CommunityRoles(Generator):
    """Base class for community roles generators."""

    def roles(self, **kwargs):
        """R."""
        raise NotImplementedError

    def communities(self, identity):
        """Communities."""
        raise NotImplementedError

    def needs(self, record=None, community_id=None, **kwargs):
        """Enabling Needs."""
        community_id = _get_community_id(record, community_id)
        if not community_id:
            print("No community id provided.")
            return []

        assert community_id, "No community id provided."
        community_id = str(community_id)

        roles = self.roles(**kwargs)
        if roles:
            needs = [CommunityRoleNeed(community_id, role) for role in roles]
            return needs
        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # Gives access to all community members.
        return dsl.Q("terms", **{"_id": self.communities(identity)})


class CommunityMembers(CommunityRoles):
    """Roles representing all members of a community."""

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles]

    def communities(self, identity):
        """Communities."""
        return [n.value for n in identity.provides if n.method == "community"]


class CommunityCurators(CommunityRoles):
    """Roles representing all curators of a community."""

    def roles(self, **kwargs):
        """Roles."""
        return [r.name for r in current_roles.can("curate")]
