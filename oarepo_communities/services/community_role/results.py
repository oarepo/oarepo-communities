from invenio_communities.communities.records.api import Community
from invenio_records_resources.services.records.results import RecordItem, RecordList

class CommunityRoleRecordItem(RecordItem):
    """Single record result."""

    def __init__(
        self,
        service,
        identity,
        community,
        role,
        errors=None,
        links_tpl=None,
        schema=None,
        expandable_fields=None,
        expand=False,
        nested_links_item=None,
    ):
        record = {
            "community": community._record,
            "role": role,
            "id": f"{community._record.id}:{role}",
        }
        super().__init__(
            service,
            identity,
            record,
            errors,
            links_tpl,
            schema,
            expandable_fields,
            expand,
            nested_links_item,
        )

    @property
    def id(self):
        """Get the record id."""
        return self._record.id


class CommunityRoleRecordList(RecordList):
    def __init__(
        self,
        service,
        identity,
        results,
        inputs,
        params=None,
        links_tpl=None,
        links_item_tpl=None,
        nested_links_item=None,
        schema=None,
        expandable_fields=None,
        expand=False,
    ):
        self._inputs = inputs
        id_to_record = {}
        for hit in results:
            id_ = hit["id"]
            if id_ not in id_to_record:
                community_record = Community.loads(hit.to_dict())
                id_to_record[id_] = community_record
        self._id_to_record = id_to_record
        super().__init__(
            service,
            identity,
            results,
            params,
            links_tpl,
            links_item_tpl,
            nested_links_item,
            schema,
            expandable_fields,
            expand,
        )

    @property
    def hits(self):
        """Iterator over the hits."""
        for community_id, community_role in self._inputs:
            # Load dump
            # record = CommunityRoleAggregate(
            #    self._id_to_record[community_id], community_role
            # )

            record = {
                "community": self._id_to_record[community_id],
                "role": community_role,
                "id": f"{community_id}:{community_role}",
            }
            # Project the record
            projection = self._schema.dump(
                record,
                context=dict(
                    identity=self._identity,
                    record=record,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, record
                )
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, record, projection)

            yield projection
