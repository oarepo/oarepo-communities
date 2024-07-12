from invenio_communities.proxies import current_communities
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_requests.resolvers.registry import ResolverRegistry
from invenio_search.engine import dsl
from oarepo_requests.resolvers.ui import OARepoUIResolver, fallback_label_result


class OARepoCommunityReferenceUIResolver(OARepoUIResolver):
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
        label = self._resolve_community_label(record, reference)
        ret = {
            "reference": reference,
            "type": "community",
            "label": label,
            "links": self._resolve_links(record),
        }
        return ret


class CommunityRoleUIResolver(OARepoCommunityReferenceUIResolver):
    def _get_id(self, result):
        # reuse reference_entity somehow?
        return f"{result['community']['id']} : {result['role']}"

    def _search_many(self, identity, values, *args, **kwargs):
        # todo this is kind of awkward but idk if it can be done better without persistently saving communityrole objects
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
        # todo we aren't using ResolverRegistry.reference_entity bc of permission validation?
        proxy = ResolverRegistry.resolve_entity_proxy(reference)
        community_reference = proxy.community_reference()
        community = super()._search_one(identity, community_reference, *args, **kwargs)
        return {"community": community, "role": proxy._parse_ref_dict_role()}

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
