#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM search mapping.

This module provides a preset that modifies search mapping to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ReviewMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        parent_mapping = {
            "mappings": {
                "properties": {
                    "parent": {
                        "properties": {
                            "review": {
                                "type": "object",
                                "properties": {
                                    "$schema": {
                                        "type": "keyword",
                                        "index": False
                                    },
                                    "id": {
                                        "type": "keyword"
                                    },
                                    "type": {
                                        "type": "keyword"
                                    },
                                    "title": {
                                        "type": "text"
                                    },
                                    "description": {
                                        "type": "text"
                                    },
                                    "status": {
                                        "type": "keyword"
                                    },
                                    "payload": {
                                        "type": "object",
                                        "dynamic": "true"
                                    },
                                    "topic": {
                                        "type": "object",
                                        "dynamic": "true"
                                    },
                                    "receiver": {
                                        "type": "object",
                                        "dynamic": "true"
                                    },
                                    "created_by": {
                                        "type": "object",
                                        "dynamic": "true"
                                    },
                                    "@v": {
                                        "type": "keyword"
                                    }
                                }
                            }

                         }
                    }
                }
            }
        }



        yield PatchJSONFile(
            "draft-mapping",
            parent_mapping,
        )