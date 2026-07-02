#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Fixture overrides that swap the API app factory for the UI one.

Scoped to this subdirectory so the sibling ``test_collections_service.py``
tests continue to boot the API app.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flask_webpackext.manifest import (
    JinjaManifest,
    JinjaManifestEntry,
    JinjaManifestLoader,
)
from invenio_app.factory import create_app as _create_app

if TYPE_CHECKING:
    from typing import Any


class _MockManifest(JinjaManifest):
    """Return a stub entry for any key so ``{{ webpack['x.js'] }}`` never errors."""

    def __getitem__(self, key: str) -> JinjaManifestEntry:
        """Return a mock manifest entry for the given key."""
        return JinjaManifestEntry(key, [key])

    def __getattr__(self, name: str) -> JinjaManifestEntry:
        """Return a mock manifest entry for the given attribute name."""
        return JinjaManifestEntry(name, [name])


class _MockManifestLoader(JinjaManifestLoader):
    """Hand back the mock manifest so tests skip a real webpack build."""

    def load(self, _filepath: str):  # type: ignore[override]  # noqa: ANN202
        """Load the mock manifest."""
        return _MockManifest()


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):  # type: ignore[no-untyped-def]
    """Use the UI factory so the collections blueprint is actually registered."""
    return _create_app


@pytest.fixture(scope="module")
def app_config(app_config: dict[str, Any]) -> dict[str, Any]:
    """Mock the webpack manifest — real builds are not part of the test path."""
    app_config["WEBPACKEXT_MANIFEST_LOADER"] = _MockManifestLoader
    return app_config
