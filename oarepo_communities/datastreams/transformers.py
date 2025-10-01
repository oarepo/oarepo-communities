#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Transformer that add default community to a record."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_vocabularies.datastreams.transformers import BaseTransformer

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_vocabularies.datastreams import StreamEntry


class SetCommunityTransformer(BaseTransformer):
    """Add community to the record."""

    def __init__(self, identity: Identity, *, community: str) -> None:
        """Initialize the transformer."""
        super().__init__()
        self.community = community
        self.identity = identity

    @override
    def apply(self, stream_entry: StreamEntry, *args: Any, **kwargs: Any) -> StreamEntry:
        stream_entry.entry.setdefault("parent", {}).setdefault("communities", {}).setdefault("default", self.community)
        return stream_entry
