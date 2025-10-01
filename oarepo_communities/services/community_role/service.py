#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Service for managing community-role pseudo records. Used in entity resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_records_resources.services.records.service import RecordService
from invenio_search.engine import dsl
from oarepo_runtime.typing import record_from_result

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask_principal import Identity
    from invenio_records_resources.services.records.results import (
        RecordItem,
        RecordList,
    )


def minimal_service[T](kept_methods: list[str]) -> Callable[[type[T]], type[T]]:
    """Convert a service to a minimal service with only the specified methods implemented."""
    kept_methods = [
        *kept_methods,
        "record_cls",
        "links_item_tpl",
        "schema",
        "result_item",
        "result_list",
    ]

    # have a look at all methods of RecordService and if they are not overriden,
    # unimplement them
    def wrapper(cls: type[T]) -> type[T]:
        for method_name in dir(cls):
            if method_name.startswith("_"):
                continue

            method = getattr(cls, method_name)
            if callable(method) and method_name not in kept_methods:
                # unimplement the method
                def unimplemented_method(self, *args, **kwargs) -> Any:  # type: ignore[] # noqa: ANN001, ANN003, ANN002
                    raise NotImplementedError(f"Please do not use this method on {cls.__name__}")

                setattr(cls, method_name, unimplemented_method)
        return cls

    return wrapper


@minimal_service(kept_methods=["read", "read_many"])
class CommunityRoleService(RecordService):
    """Service for managing community-role records."""

    @override
    def read(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        action: str = "read",
        **kwargs: Any,
    ) -> RecordItem:
        community_id = id_.split(":")[0].strip()
        role = id_.split(":")[1].strip()
        community = current_communities.service.read(identity, community_id, **kwargs)
        result = {
            "community": record_from_result(community),
            "role": role,
            "id": f"{community_id}:{role}",
        }
        return self.result_item(self, identity, record=result, links_tpl=self.links_item_tpl)

    @override
    def read_many(
        self,
        identity: Identity,
        ids: list[str],
        fields: list[str] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        if not ids:
            return self.result_list(
                identity,
                results=[],
                schema=self.schema,
            )

        community_and_role_split_inputs: set[tuple[str, str]] = set()
        for x in ids:
            community_id, role = x.split(":")
            community_and_role_split_inputs.add((community_id.strip(), role.strip()))

        community_ids = {x[0] for x in community_and_role_split_inputs}

        query = dsl.Q("terms", id=community_ids)

        communities_search_results = current_communities.service._read_many(  # noqa: SLF001
            identity, query, fields, len(community_ids), **kwargs
        )

        id_to_record = {
            hit["id"]: Community.loads(hit.to_dict())  # type: ignore[call-arg]
            for hit in communities_search_results
        }

        results = [
            {
                "community": id_to_record[community_id],
                "role": community_role,
                "id": f"{community_id}:{community_role}",
            }
            for community_id, community_role in community_and_role_split_inputs
        ]

        return self.result_list(
            identity,
            results=results,
            schema=self.schema,
        )
