# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM Community Records Service."""

from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import RecordService, ServiceSchemaWrapper
from invenio_records_resources.services.uow import unit_of_work
from invenio_search.engine import dsl

from oarepo_communities.utils.utils import (
    get_associated_service,
    get_global_search_service,
    get_global_user_search_service,
    get_service_from_schema_type,
)

# from invenio_rdm_records.proxies import current_record_communities_service


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

    @property
    def community_cls(self):
        """Factory for creating a community class."""
        return self.config.community_cls

    @property
    def record_cls(self):
        """Factory for creating a community class."""
        return self.config.record_cls

    @property
    def draft_cls(self):
        """Factory for creating a community class."""
        return self.config.draft_cls

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
        community = self.community_cls.pid.resolve(community_id)
        self.require_permission(
            identity, "search", community=community
        )  # different permission instead?
        params = params or {}

        community_filter = dsl.Q(
            "term", **{"parent.communities.ids.keyword": str(community.id)}
        )
        if extra_filter is not None:
            community_filter = community_filter & extra_filter
        return get_global_search_service().global_search(
            identity, params, extra_filter=community_filter, community=community
        )

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
        community = self.community_cls.pid.resolve(community_id)
        self.require_permission(identity, "search_drafts", community=community)
        params = params or {}

        community_filter = dsl.Q(
            "term", **{"parent.communities.ids.keyword": str(community.id)}
        )
        if extra_filter is not None:
            community_filter = community_filter & extra_filter

        return get_global_user_search_service().global_search(
            identity, params, extra_filter=community_filter, community=community
        )

    @unit_of_work()
    def create_in_community(
        self, identity, community_id, data, model=None, uow=None, expand=False
    ):
        # should the dumper put the entries thing into search? ref CommunitiesField#110, not in rdm; it is in new rdm, i had quite old version
        # community_id may be the slug coming from resource
        if model:
            record_service = current_service_registry.get(model)
        else:
            record_service = get_service_from_schema_type(data["$schema"])
        if not record_service:
            raise ValueError(f"No service found for requested model {model}.")
        community = current_communities.service.record_cls.pid.resolve(community_id)
        self.require_permission(identity, "create_in_community", community=community)

        record = record_service.create(identity, data, uow=uow, expand=expand)._record

        record_communities_service = get_associated_service(
            record_service, "record_communities"
        )

        # todo this should probably be reconcetualized, how to return the actual record item with the updated parent?
        record_with_community_in_parent = record_communities_service.include(
            record,
            community_id,
            record_service=record_service,
            uow=uow,
        )
        record_item = record_service.result_item(
            record_service,
            identity,
            record_with_community_in_parent,
            links_tpl=record_service.links_item_tpl,
            expandable_fields=record_service.expandable_fields,
            expand=expand,
        )

        return record_item
