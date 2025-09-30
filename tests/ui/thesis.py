#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Thesis UI resource for tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import marshmallow as ma
from flask_resources import BaseListSchema, JSONSerializer, MarshmallowSerializer
from oarepo_ui.resources import (
    BabelComponent,
    PermissionsComponent,
    RecordsUIResourceConfig,
)
from oarepo_ui.resources.components.bleach import AllowedHtmlTagsComponent
from oarepo_ui.resources.components.custom_fields import CustomFieldsComponent

if TYPE_CHECKING:
    from collections.abc import Mapping


class ModelSchema(ma.Schema):
    """Schema for serializing the model."""

    title = ma.fields.String()

    class Meta:
        """Meta class to include unknown fields."""

        unknown = ma.INCLUDE


class ModelUISerializer(MarshmallowSerializer):
    """UI JSON serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelSchema,
            list_schema_cls=BaseListSchema,
            schema_context={"object_key": "ui"},
        )


class ThesisUIResourceConfig(RecordsUIResourceConfig):
    """Thesis UI resource config for tests."""

    api_service = "thesis"  # must be something included in oarepo, as oarepo is used in tests

    blueprint_name = "thesis"
    url_prefix = "/thesis"
    ui_serializer_class = ModelUISerializer
    templates: Mapping[str, str] = {
        **RecordsUIResourceConfig.templates,
    }

    components = (
        BabelComponent,
        PermissionsComponent,
        AllowedHtmlTagsComponent,
        CustomFieldsComponent,
    )
