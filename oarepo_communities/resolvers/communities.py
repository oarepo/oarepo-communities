from invenio_communities.communities.records.api import Community
from invenio_db import db
from oarepo import __version__ as oarepo_version

from oarepo_communities.permissions.generators import needs_from_workflow
from oarepo_communities.records.models import CommunityWorkflowModel

if oarepo_version.split(".")[0] == "11":
    from invenio_communities.communities.resolver import (
        CommunityPKProxy,
        CommunityResolver,
    )
else:
    from invenio_communities.communities.entity_resolvers import (
        CommunityPKProxy,
        CommunityResolver,
    )

from invenio_communities.communities.services.config import CommunityServiceConfig


class OARepoCommunityPKProxy(CommunityPKProxy):
    def get_needs(self, ctx=None):
        comm_id = str(self._parse_ref_dict_id())
        workflow = (
            db.session.query(CommunityWorkflowModel.workflow)
            .filter(CommunityWorkflowModel.community_id == comm_id)
            .one()
        )
        needs = needs_from_workflow(
            workflow[0], "draft", ctx["request_type"], "receivers", community_id=comm_id
        )
        return needs


class OARepoCommunityResolver(CommunityResolver):
    type_id = "community"

    def __init__(self):
        """Initialize the default record resolver."""
        super(CommunityResolver, self).__init__(
            Community,
            CommunityServiceConfig.service_id,
            type_key=self.type_id,
            proxy_cls=OARepoCommunityPKProxy,
        )
