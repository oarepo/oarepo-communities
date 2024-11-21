from __future__ import annotations


from typing import TYPE_CHECKING

from invenio_communities.proxies import current_communities, current_roles
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_requests.resolvers.ui import OARepoUIResolver, fallback_label_result, UIResolvedReference
from oarepo_runtime.i18n import gettext as _

if TYPE_CHECKING:
    from oarepo_requests.typing import EntityReference

class CommunityRoleUIResolver(OARepoUIResolver):
    def _get_community_label(self, record, reference):
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

    def _get_role_label(self, role):
        return current_roles[role].title

    def _get_id(self, result):
        # reuse reference_entity somehow?
        return f"{result['community']['id']}:{result['role']}"

    def _search_many(self, identity, values, *args, **kwargs):
        if not values:
            return []
        values_map = {
            x.split(":")[0].strip(): x.split(":")[1].strip() for x in values
        }  # can't use proxy here due values not being on form of ref dicts
        community_ids = values_map.keys()
        results = current_communities.service.read_many(identity, community_ids).hits
        actual_results = []
        for result in results:
            actual_result = {"community": result, "role": values_map[result["id"]]}
            actual_results.append(actual_result)
        return actual_results

    def _search_one(self, identity, _id, *args, **kwargs):
        reference = {self.reference_type: _id}
        proxy = ResolverRegistry.resolve_entity_proxy(reference)
        community_id, role = proxy._parse_ref_dict()
        try:
            community = current_communities.service.read(identity, community_id).data
        except PermissionDeniedError:
            return None
        return {"community": community, "role": role}

    def _get_entity_ui_representation(
        self, entity: dict, reference: EntityReference
    ) -> UIResolvedReference:

        community_record = entity["community"]
        community_label = self._get_community_label(community_record, reference)
        role_label = self._get_role_label(entity["role"])

        return UIResolvedReference(
            reference = reference,
            type = "community role",
            label = _(
                "%(role)s of %(community)s", role=role_label, community=community_label
            ),
            links = self._extract_links_from_resolved_reference(community_record),
        )