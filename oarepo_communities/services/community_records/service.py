# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM Community Records Service."""

from invenio_communities.proxies import current_communities
from invenio_records_resources.services import (
    LinksTemplate,
    RecordService,
    ServiceSchemaWrapper,
)
from invenio_records_resources.services.uow import unit_of_work
from invenio_search.engine import dsl

# from invenio_rdm_records.proxies import current_record_communities_service


class CommunityRecordsService(RecordService):
    """Community records service.

    The record communities service is in charge of managing the records of a given community.
    """

    def __init__(self, config, record_service=None, record_communities_service=None):
        super().__init__(config)
        self.record_service = record_service
        self.record_communities_service = record_communities_service

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
        self.require_permission(identity, "search", community=community)
        params = params or {}

        community_filter = dsl.Q(
            "term", **{"parent.communities.ids.keyword": str(community.id)}
        )
        if extra_filter is not None:
            community_filter = community_filter & extra_filter

        search = self._search(
            "search",
            identity,
            params,
            search_preference,
            extra_filter=community_filter,
            permission_action="read",
            **kwargs,
        )
        search_result = search.execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(
                self.config.links_search_community_records,
                context={
                    "args": params,
                    "id": str(community.id),
                },
            ),
            links_item_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    def search_drafts(
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

        search = self._search(
            "search_drafts",
            identity,
            params,
            search_preference,
            record_cls=self.config.draft_cls,
            extra_filter=community_filter,
            permission_action="read_draft",
            **kwargs,
        )
        search_result = search.execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(
                self.config.links_search_community_records,
                context={
                    "args": params,
                    "id": str(community.id),
                },
            ),
            links_item_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    """
    def _remove(self, community, record, identity):
        data = dict(communities=[dict(id=str(community.id))])
        _, errors = self.record_communities_service.remove(
            identity, id_=record.pid.pid_value, data=data
        )

        return errors
    
    @unit_of_work()
    def delete(self, identity, community_id, data, revision_id=None, uow=None):
        community = self.community_cls.pid.resolve(community_id)

        self.require_permission(
            identity, "remove_records_from_community", community=community
        )

        valid_data, errors = self.community_record_schema.load(
            data,
            context={
                "identity": identity,
                "max_number": self.config.max_number_of_removals,
            },
            raise_errors=True,
        )
        records_dict = valid_data["records"]

        for record_dict in records_dict:
            record_id = record_dict["id"]
            try:
                record = self.record_cls.pid.resolve(record_id)
                errors += self._remove(community, record, identity)
            except PIDDoesNotExistError:
                errors.append(
                    {
                        "record": record_id,
                        "message": "The record does not exist.",
                    }
                )
            except PermissionDeniedError:
                errors.append(
                    {
                        "record": record_id,
                        "message": "Permission denied.",
                    }
                )

        return errors
    """

    @unit_of_work()
    def create_in_community(self, identity, community_id, data, uow=None, expand=False):
        # community_id may be the slug coming from resource
        community = current_communities.service.record_cls.pid.resolve(community_id)
        self.require_permission(identity, "create_in_community", community=community)
        record_service = self.record_service
        # todo add record service in mb ext
        record = record_service.create(identity, data, uow=uow, expand=expand)._record

        # todo this should probably be reconceptualized, how to return the actual record item with the updated parent?
        record_with_community_in_parent = self.record_communities_service.include(
            record,
            community,
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

    """
    @unit_of_work()
    def community_submission(self, identity, community_id, record_id, uow=None, expand=False):
        community = current_communities.service.record_cls.pid.resolve(community_id)
        record = self.record_service.config.record_cls.pid.resolve(record_id)

        # todo do i need separate permission on who can create request; ie. authenticated users
        #self.require_permission(identity, "submit_to_community", community=community)

        already_included = community_id in record.parent.communities
        if already_included:
            raise CommunityAlreadyExists()

        existing_request_id = _exists(identity, community_id, record)
        if existing_request_id:
            raise OpenRequestAlreadyExists(existing_request_id)

        # todo request type mb generated
        type_ = current_request_type_registry.lookup(CommunitySubmissionRequestType.type_id)
        receiver = {"oarepo_community": community_id}

        request_item = current_requests_service.create(
            identity,
            {},
            type_,
            receiver,
            topic=record,
            uow=uow,
        )

        # create review request
        #request_item = current_rdm_records.community_inclusion_service.submit(
        #    identity, record, community, request_item._request, comment, uow
        #)
        # include directly when allowed
        #if not require_review:
        #    request_item = current_rdm_records.community_inclusion_service.include(
        #        identity, community, request_item._request, uow
        #    )

        request_item = current_requests_service.execute_action(
            identity, request_item.id, "submit", uow=uow
        )
        return request_item
        """
