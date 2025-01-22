from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask_principal import Identity


def community_role_mappings(identity: Identity) -> list[dict[str, str]]:
    community_roles = [
        (n.value, n.role) for n in identity.provides if n.method == "community"
    ]
    return [
        {"community_role": f"{community_role[0]}:{community_role[1]}"}
        for community_role in community_roles
    ]
