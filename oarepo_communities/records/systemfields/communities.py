from invenio_communities.records.records.systemfields.communities.context import (
    CommunitiesFieldContext,
)
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin

COMMUNITIES_MAPPING = {
    "parent": {
        "properties": {
            "communities": {
                "properties": {
                    "ids": {"type": "keyword"},
                    "default": {"type": "keyword"},
                }
            }
        }
    }
}


class OARepoCommunitiesFieldContext(MappingSystemFieldMixin, CommunitiesFieldContext):
    @property
    def mapping(self):
        return COMMUNITIES_MAPPING
