from invenio_communities.proxies import current_communities
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_requests.resolvers.registry import ResolverRegistry
from invenio_search.engine import dsl
from oarepo_requests.resolvers.ui import OARepoUIResolver, fallback_label_result


class CommunityRoleUIResolver(OARepoUIResolver):
    def _resolve_community_label(self, record, reference):
        if (
            "metadata" not in record or "title" not in record["metadata"]
        ):  # username undefined?
            if "slug" in record:
                label = record["slug"]
            else:
                label = fallback_label_result(reference)
        else:
            label = record["metadata"]["title"]
        return label

    def _get_id(self, result):
        # reuse reference_entity somehow?
        return f"{result['community']['id']} : {result['role']}"

    def _search_many(self, identity, values, *args, **kwargs):
        if not values:
            return []
        values_map = {
            x.split(":")[0].strip(): x.split(":")[1].strip() for x in values
        }  # can't use proxy here due values not being on form of ref dicts
        search_values = values_map.keys()
        service = current_communities.service
        filter = dsl.Q("terms", **{"id": list(search_values)})
        results = list(service.search(identity, extra_filter=filter).hits)
        actual_results = []
        for result in results:
            actual_result = {"community": result, "role": values_map[result["id"]]}
            actual_results.append(actual_result)
        return actual_results

    def _search_one(self, identity, reference, *args, **kwargs):
        proxy = ResolverRegistry.resolve_entity_proxy(reference)
        community_id, role = proxy._parse_ref_dict()
        try:
            community = current_communities.service.read(identity, community_id).data
        except PermissionDeniedError:
            return None
        return {"community": community, "role": role}

    def _resolve(self, record, reference):
        community_record = record["community"]
        label = self._resolve_community_label(community_record, reference)
        ret = {
            "reference": reference,
            "type": "community role",
            "label": f"{label} : {record['role']}",
            "links": self._resolve_links(community_record),
        }
        return ret
