#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""oarepo-communities webpack bundle."""

from __future__ import annotations  # pragma: no cover

from invenio_assets.webpack import WebpackThemeBundle  # pragma: no cover

theme = WebpackThemeBundle(  # pragma: no cover
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": {
            "entry": {},
            "dependencies": {},
            "devDependencies": {},
            "aliases": {"@js/oarepo_communities": "./js/oarepo_communities"},
        }
    },
)
