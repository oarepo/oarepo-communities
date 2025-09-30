#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_record_with_community_data(communities):
    community_aaa = str(communities["aaa"].id)
    community_bbb = str(communities["bbb"].id)
    return {
        "parent": {
            "communities": {
                "ids": {community_aaa, community_bbb},
                "default": community_aaa,
            }
        }
    }


@pytest.fixture
def as_comparable_dict():
    def _as_comparable(d: Any) -> Any:
        if isinstance(d, dict):
            return {k: _as_comparable(v) for k, v in sorted(d.items())}
        if isinstance(d, (list, tuple)):
            return {_as_comparable(v) for v in d}  # type: ignore[reportUnhashable]
        return d

    return _as_comparable
