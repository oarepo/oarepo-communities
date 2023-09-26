from functools import lru_cache

from invenio_access.permissions import system_identity
from invenio_communities import current_communities
import cachetools

@cachetools.cached(cache=cachetools.TTLCache(maxsize=1028, ttl=360))
def permissions_cache(community_id):
    return current_communities.service.read(system_identity, community_id).data["custom_fields"]["permissions"]