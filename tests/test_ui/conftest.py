#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Pytest configuration for oarepo-communities UI tests."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from flask import Blueprint, Flask
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app as _create_app
from invenio_communities.proxies import current_communities
from invenio_vocabularies.proxies import current_service as vocabulary_service

# Fake blueprint to provide missing endpoints during tests
fake_rdm_users_bp = Blueprint("invenio_app_rdm_users", __name__)


@fake_rdm_users_bp.route("/me/communities")
def communities():
    """Fake endpoint for user communities."""
    return ""


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""

    def factory(**config: Any) -> Flask:
        app = _create_app(**config)
        app.register_blueprint(fake_rdm_users_bp)
        return app

    return factory


@pytest.fixture(scope="module")
def community_service(app):
    """Community service."""
    return current_communities.service


@pytest.fixture(scope="module")
def system_identity_fixture():
    """System identity fixture."""
    return system_identity


@pytest.fixture(scope="module")
def vocabularies_service(app):
    """Vocabularies service."""
    return vocabulary_service


@pytest.fixture(scope="module")
def community_type_type(system_identity_fixture, vocabularies_service):
    """Create and retrieve a language vocabulary type."""
    return vocabularies_service.create_type(system_identity_fixture, "communitytypes", "comtyp")


@pytest.fixture
def fake_manifest(app):
    python_path = Path(sys.executable)
    invenio_instance_path = python_path.parent.parent / "var" / "instance"
    manifest_path = invenio_instance_path / "static" / "dist"
    manifest_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).parent / "manifest.json", manifest_path / "manifest.json")
