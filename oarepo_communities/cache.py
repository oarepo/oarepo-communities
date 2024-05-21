from cachetools import TTLCache, cached
from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from invenio_search.engine import dsl


@cached(cache=TTLCache(maxsize=1028, ttl=600))
def permissions_cache(community_id):
    try:
        return current_communities.service.read(system_identity, community_id).data[
            "custom_fields"
        ]["permissions"]
    except KeyError:
        # todo log
        return {}


@cached(cache=TTLCache(maxsize=1028, ttl=600))
def allowed_communities_cache(user_type, action):
    try:
        filter = dsl.Q(
            "term", **{f"custom_fields.permissions.{user_type}.can_{action}": True}
        )
        result = current_communities.service.search(
            system_identity, extra_filter=filter
        )
        result = {hit["id"] for hit in list(result.hits)}
        return result
    except KeyError:
        return {}


def aai_mapping(community_id):
    try:
        return current_communities.service.read(system_identity, community_id).data[
            "custom_fields"
        ]["aai_mapping"]
    except KeyError:
        return {}
