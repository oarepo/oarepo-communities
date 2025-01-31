# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

# from invenio_drafts_resources.services.records.service import RecordService
from invenio_records_resources.services import ServiceSchemaWrapper
from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.uow import unit_of_work
from invenio_search.engine import dsl
from oarepo_global_search.proxies import current_global_search_service

from oarepo_communities.utils import (
    get_service_by_urlprefix,
    get_service_from_schema_type,
)

# from oarepo_runtime.datastreams.utils import get_service_from_schema_type

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_records_resources.services.base.links import LinksTemplate
    from invenio_records_resources.services.records.results import (
        RecordItem,
        RecordList,
    )
    from invenio_records_resources.services.records.service import RecordService
    from invenio_records_resources.services.uow import UnitOfWork
    from opensearch_dsl.query import Query


class CommunityRecordsService(Service):
    """Community records service.

    The record communities service is in charge of managing the records of a given community.
    """

    @property
    def community_record_schema(self) -> ServiceSchemaWrapper:
        """Returns the community schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.community_record_schema)

    def _search(
        self,
        identity: Identity,
        community_id: str,
        search_service: RecordService,
        search_method: str,
        links_template: LinksTemplate,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        extra_filter: Query | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        params = params or {}
        default_filter = dsl.Q("term", **{"parent.communities.ids": community_id})
        if extra_filter is not None:
            default_filter = default_filter & extra_filter
        ret = getattr(search_service, search_method)(
            identity, params, extra_filter=default_filter
        )
        links_template.context["args"] |= ret._links_tpl.context["args"]
        ret._links_tpl = links_template
        return ret

    def search(
        self,
        identity: Identity,
        community_id: str,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        extra_filter: Query | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        params_copy = copy.deepcopy(params)
        facets = params_copy.pop("facets")
        params_copy.update(facets)
        return self._search(
            identity,
            community_id,
            search_service=current_global_search_service,
            search_method="search",
            links_template=LinksTemplate(
                self.config.links_search_community_records,
                context={"args": params_copy, "id": community_id},
            ),
            params=params,
            search_preference=search_preference,
            extra_filter=extra_filter,
            expand=expand,
            **kwargs,
        )

    def search_model(
        self,
        identity: Identity,
        community_id: str,
        model_url_name: str,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        extra_filter: Query | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:

        return self._search(
            identity,
            community_id,
            search_service=get_service_by_urlprefix(model_url_name),
            search_method="search",
            links_template=LinksTemplate(
                self.config.links_search_community_model_records,
                context={"args": params, "id": community_id, "model": model_url_name},
            ),
            params=params,
            search_preference=search_preference,
            extra_filter=extra_filter,
            expand=expand,
            **kwargs,
        )

    def user_search(
        self,
        identity: Identity,
        community_id: str,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        extra_filter: Query | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:

        params_copy = copy.deepcopy(params)
        facets = params_copy.pop("facets")
        params_copy.update(facets)
        return self._search(
            identity,
            community_id,
            search_service=current_global_search_service,
            search_method="search_drafts",
            links_template=LinksTemplate(
                self.config.links_search_community_user_records,
                context={"args": params_copy, "id": community_id},
            ),
            params=params,
            search_preference=search_preference,
            extra_filter=extra_filter,
            expand=expand,
            **kwargs,
        )

    def user_search_model(
        self,
        identity: Identity,
        community_id: str,
        model_url_name: str,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        extra_filter: Query | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:

        return self._search(
            identity,
            community_id,
            search_service=get_service_by_urlprefix(model_url_name),
            search_method="search_drafts",
            links_template=LinksTemplate(
                self.config.links_search_community_model_user_records,
                context={"args": params, "id": community_id, "model": model_url_name},
            ),
            params=params,
            search_preference=search_preference,
            extra_filter=extra_filter,
            expand=expand,
            **kwargs,
        )

    @unit_of_work()
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        community_id: str,
        model: str = None,
        uow: UnitOfWork | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordItem:
        # should the dumper put the entries thing into search? ref CommunitiesField#110, not in rdm; it is in new rdm, i had quite old version
        # community_id may be the slug coming from resource
        if model:
            record_service = get_service_by_urlprefix(model)
        else:
            record_service = get_service_from_schema_type(data["$schema"])
        if not record_service:
            raise ValueError(f"No service found for requested model {model}.")
        data.setdefault("parent", {}).setdefault("communities", {})[
            "default"
        ] = community_id
        result_item = record_service.create(
            identity, data, uow=uow, expand=expand, **kwargs
        )
        return result_item
