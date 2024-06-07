from invenio_communities.communities.records.api import Community
from oarepo import __version__ as oarepo_version

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
        """Return community member need."""
        comid = str(self._parse_ref_dict_id())
        needs = []
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
