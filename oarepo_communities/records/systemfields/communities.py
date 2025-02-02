from invenio_communities.records.records.systemfields.communities.context import (
    CommunitiesFieldContext,
)
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin

COMMUNITIES_MAPPING = {
    "communities": {
        "properties": {
            "ids": {"type": "keyword"},
            "default": {"type": "keyword"},
        }
    }
}


class OARepoCommunitiesFieldContext(MappingSystemFieldMixin, CommunitiesFieldContext):
    @property
    def mapping(self) -> dict:
        return COMMUNITIES_MAPPING
