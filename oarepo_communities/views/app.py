#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint

from oarepo_communities.resolvers.communities import CommunityRoleResolver

if TYPE_CHECKING:
    from flask import Blueprint, Flask
    from flask.blueprints import BlueprintSetupState


def create_app_blueprint(app: Flask) -> Blueprint:
    """Create a blueprint for the communities endpoint.

    :param app: Flask application
    """
    blueprint = Blueprint("oarepo_communities_app", __name__, url_prefix="/communities/")
    blueprint.record_once(register_community_role_entity_resolver)
    return blueprint


def register_community_role_entity_resolver(state: BlueprintSetupState) -> None:
    app = state.app
    requests = app.extensions["invenio-requests"]
    requests.entity_resolvers_registry.register_type(CommunityRoleResolver())
