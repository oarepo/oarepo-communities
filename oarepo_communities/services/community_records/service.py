# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM Community Records Service."""

from invenio_communities.proxies import current_communities
from invenio_drafts_resources.services.records.service import RecordService
from invenio_records_resources.services import ServiceSchemaWrapper
from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.uow import unit_of_work
from invenio_search.engine import dsl

from oarepo_communities.utils.utils import (
    get_global_search_service,
    get_global_user_search_service,
    get_service_by_urlprefix,
    get_service_from_schema_type,
)

# from oarepo_runtime.datastreams.utils import get_service_from_schema_type


class CommunityRecordsService(RecordService):
    """Community records service.

    The record communities service is in charge of managing the records of a given community.
    """

    def __init__(self, config, record_service=None):
        super().__init__(config)
        self.record_service = record_service

    @property
    def community_record_schema(self):
        """Returns the community schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.community_record_schema)

    def search(
        self,
        identity,
        community_id,
        params=None,
        search_preference=None,
        extra_filter=None,
        expand=False,
        **kwargs,
    ):
        params = params or {}
        default_filter = dsl.Q("term", **{"parent.communities.ids": community_id})
        if extra_filter is not None:
            default_filter = default_filter & extra_filter
        ret = get_global_search_service().global_search(
            identity, params, extra_filter=default_filter
        )
        ret._links_tpl = LinksTemplate(
            self.config.links_search_community_records,
            context={"args": params, "id": community_id},
        )
        return ret

    def search_model(
        self,
        identity,
        community_id,
        model_url,
        params=None,
        search_preference=None,
        extra_filter=None,
        expand=False,
        **kwargs,
    ):
        # todo generate correct links?
        params = params or {}
        default_filter = dsl.Q("term", **{"parent.communities.ids": community_id})
        if extra_filter is not None:
            default_filter = default_filter & extra_filter
        service = get_service_by_urlprefix(model_url)
        return service.search(identity, params, extra_filter=default_filter)

    def user_search(
        self,
        identity,
        community_id,
        params=None,
        search_preference=None,
        extra_filter=None,
        expand=False,
        **kwargs,
    ):
        params = params or {}
        default_filter = dsl.Q("term", **{"parent.communities.ids": community_id})
        if extra_filter is not None:
            default_filter = default_filter & extra_filter

        return get_global_user_search_service().global_search(
            identity, params, extra_filter=default_filter
        )

    def user_search_model(
        self,
        identity,
        community_id,
        model_url,
        params=None,
        search_preference=None,
        extra_filter=None,
        expand=False,
        **kwargs,
    ):
        params = params or {}
        default_filter = dsl.Q("term", **{"parent.communities.ids": community_id})
        if extra_filter is not None:
            default_filter = default_filter & extra_filter

        service = get_service_by_urlprefix(model_url)
        return service.search_drafts(identity, params, extra_filter=default_filter)

    @unit_of_work()
    def create_in_community(
        self, identity, community_id, data, model=None, uow=None, expand=False
    ):
        # should the dumper put the entries thing into search? ref CommunitiesField#110, not in rdm; it is in new rdm, i had quite old version
        # community_id may be the slug coming from resource
        if model:
            record_service = get_service_by_urlprefix(model)
        else:
            record_service = get_service_from_schema_type(data["$schema"])
        if not record_service:
            raise ValueError(f"No service found for requested model {model}.")
        community = current_communities.service.record_cls.pid.resolve(community_id)

        return record_service.create(
            identity, data, uow=uow, expand=expand, community=community
        )
