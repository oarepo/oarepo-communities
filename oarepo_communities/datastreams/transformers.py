#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any, override

from flask_principal import Identity
from invenio_vocabularies.datastreams import StreamEntry
from invenio_vocabularies.datastreams.transformers import BaseTransformer


class SetCommunityTransformer(BaseTransformer):
    """Add community to the record."""

    def __init__(self, identity: Identity, *, community: str, **kwargs: Any) -> None:
        """Initialize the transformer."""
        super().__init__()
        self.community = community
        self.identity = identity

    @override
    def apply(self, stream_entry: StreamEntry, *args: Any, **kwargs: Any) -> StreamEntry:
        stream_entry.entry.setdefault("parent", {}).setdefault("communities", {}).setdefault("default", self.community)
        return stream_entry
