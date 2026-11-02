# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
