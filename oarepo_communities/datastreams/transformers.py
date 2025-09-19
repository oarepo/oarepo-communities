#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from oarepo_runtime.datastreams.transformers import BaseTransformer
from oarepo_runtime.datastreams.types import StreamBatch


class SetCommunityTransformer(BaseTransformer):
    """Add community to the record."""

    def __init__(self, identity, *, community, **kwargs) -> None:
        super().__init__()
        self.community = community
        self.identity = identity

    def apply(self, batch: StreamBatch, *args, **kwargs) -> StreamBatch:
        if not len(batch.entries):
            return batch
        for entry in batch.entries:
            entry.entry.setdefault("parent", {}).setdefault("communities", {}).setdefault("default", self.community)
