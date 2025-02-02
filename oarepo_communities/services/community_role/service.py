from functools import cached_property
from typing import Iterable

from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from invenio_search.engine import dsl


class CommunityRoleService(Service):
    @cached_property
    def community_service(self):
        return current_communities.service

    @property
    def record_cls(self):
        return self.config.record_cls

    @property
    def links_item_tpl(self):
        """Item links template."""
        return LinksTemplate(
            self.config.links_item,
        )

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    def read(self, identity, id_: str, **kwargs):
        community_id = id_.split(":")[0].strip()
        role = id_.split(":")[1].strip()
        community = self.community_service.read(identity, community_id, **kwargs)
        result = {
            "community": community._record,
            "role": role,
            "id": f"{community_id}:{role}",
        }
        return self.result_item(
            self, identity, record=result, links_tpl=self.links_item_tpl
        )

    def read_many(self, identity, ids: Iterable[str], fields=None, **kwargs):
        if not ids:
            return []
        community_and_role_split_inputs = {
            (x.split(":")[0].strip(), x.split(":")[1].strip()) for x in ids
        }
        community_ids = {x[0] for x in community_and_role_split_inputs}

        clauses = []
        for id_ in community_ids:
            clauses.append(dsl.Q("term", **{"id": id_}))
        query = dsl.Q("bool", minimum_should_match=1, should=clauses)

        communities_search_results = self.community_service._read_many(
            identity, query, fields, len(community_ids), **kwargs
        )

        results = []

        id_to_record = {}
        for hit in communities_search_results:
            id_ = hit["id"]
            if id_ not in id_to_record:
                community_record = Community.loads(hit.to_dict())
                id_to_record[id_] = community_record

        for community_id, community_role in community_and_role_split_inputs:
            record = {
                "community": id_to_record[community_id],
                "role": community_role,
                "id": f"{community_id}:{community_role}",
            }
            results.append(record)

        return self.result_list(
            self,
            identity,
            results=results,
            links_item_tpl=self.links_item_tpl,
        )
