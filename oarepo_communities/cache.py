from cachetools import TTLCache, cached
from invenio_access.permissions import system_identity
from invenio_communities import current_communities


@cached(cache=TTLCache(maxsize=1028, ttl=600))
def permissions_cache(community_id):
    try:
        return current_communities.service.read(system_identity, community_id).data[
            "custom_fields"
        ]["permissions"]
    except KeyError:
        # todo log
        return {}


def aai_mapping(community_id):
    try:
        return current_communities.service.read(system_identity, community_id).data[
            "custom_fields"
        ]["aai_mapping"]
    except KeyError:
        # todo log
        return {}
