from invenio_communities.proxies import current_communities
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_search.engine import dsl
from oarepo_requests.resolvers.ui import OARepoUIResolver, fallback_label_result


class OARepoCommunityReferenceUIResolver(OARepoUIResolver):
    def _get_id(self, result):
        return result["id"]

    def _search_many(self, identity, values, *args, **kwargs):
        if not values:
            return []
        service = current_communities.service
        filter = dsl.Q("terms", **{"id": list(values)})
        return list(service.search(identity, extra_filter=filter).hits)

    def _search_one(self, identity, reference, *args, **kwargs):
        value = list(reference.values())[0]
        try:
            community = current_communities.service.read(identity, value).data
            return community
        except PermissionDeniedError:
            return None

    def _resolve(self, record, reference):
        if (
            "metadata" not in record or "title" not in record["metadata"]
        ):  # username undefined?
            if "slug" in record:
                label = record["slug"]
            else:
                label = fallback_label_result(reference)
        else:
            label = record["metadata"]["title"]
        ret = {
            "reference": reference,
            "type": "community",
            "label": label,
        }
        if "links" in record and "self" in record["links"]:
            ret["link"] = record["links"]["self"]
        return ret
