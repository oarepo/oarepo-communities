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

if TYPE_CHECKING:
    from flask_principal import Identity


def community_role_mappings(identity: Identity) -> list[dict[str, str]]:
    community_roles = [(n.value, n.role) for n in identity.provides if n.method == "community"]
    return [{"community_role": f"{community_role[0]}:{community_role[1]}"} for community_role in community_roles]
