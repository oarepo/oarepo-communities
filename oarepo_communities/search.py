# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from elasticsearch_dsl.query import Bool, Q
from flask import request
from invenio_records_rest.facets import terms_filter
from oarepo_enrollment_permissions import RecordsSearchMixin

from oarepo_communities.proxies import current_oarepo_communities


class CommunitySearchMixin(RecordsSearchMixin):
    """RecordsSearchMixin that limits results to community scope."""

    class Meta:
        @staticmethod
        def default_filter_factory(search=None, **kwargs):
            return CommunitySearchMixin.community_filter(),

        @staticmethod
        def _default_anonymous_filter_factory(search=None, **kwargs):
            return CommunitySearchMixin.Meta.default_filter_factory(search, **kwargs)

        doc_types = ['_doc']
        default_anonymous_filter = _default_anonymous_filter_factory
        default_authenticated_filter = default_filter_factory

    @staticmethod
    def community_filter():
        request_community = request.view_args['community_id']

        return Bool(should=[
            Q('term', **{current_oarepo_communities.primary_community_field: request_community}),
            terms_filter(current_oarepo_communities.communities_field)([request_community])
        ], minimum_should_match=1)


CommunitySearch = CommunitySearchMixin
