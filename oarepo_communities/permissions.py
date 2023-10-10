from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=1028, ttl=600))
def permissions_cache(community_id):
    return current_communities.service.read(system_identity, community_id).data["custom_fields"]["permissions"]

def usermap(community_id):
    return current_communities.service.read(system_identity, community_id).data["custom_fields"]["usermap"]

