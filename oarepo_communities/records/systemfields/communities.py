#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
