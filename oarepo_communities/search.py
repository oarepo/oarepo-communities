# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import functools
import re

from boltons.typeutils import classproperty
from elasticsearch_dsl.query import Bool, Q
from flask import request
from flask_login import current_user
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.query import es_search_factory
from oarepo_enrollment_permissions import RecordsSearchMixin
from oarepo_search.query_parsers import query_parser

from oarepo_communities.constants import STATE_PUBLISHED, STATE_APPROVED
from oarepo_communities.permissions import community_member_permission_impl, community_curator_permission_impl, \
    community_publisher_permission_impl
from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.utils import community_id_from_request, current_user_communities


class CommunitySearchMixin(RecordsSearchMixin):
    """Base class implementing search in community record collections."""
    LIST_SOURCE_FIELDS = []
    HIGHLIGHT_FIELDS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html#return-agg-type
        self._params = {'typed_keys': True}
        self._source = self._source = type(self).LIST_SOURCE_FIELDS
        for k, v in type(self).HIGHLIGHT_FIELDS.items():
            self._highlight[k] = v or {}

    class ActualMeta:
        outer_class = None
        doc_types = ['_doc']

        @classproperty
        def default_anonymous_filter(cls):
            if not community_id_from_request():
                return Q('term', state=STATE_PUBLISHED)

            return Bool(must=[
                cls.outer_class.Meta.default_request_community_filter(),
                Q('term', state=STATE_PUBLISHED)])

        @classproperty
        def default_authenticated_filter(cls):
            return Bool(must=[
                cls.outer_class.Meta.default_request_community_filter(),
                Q('terms', state=[STATE_APPROVED, STATE_PUBLISHED])])

        @classproperty
        def default_any_filter(cls):
            return cls.outer_class.Meta.default_anonymous_filter

        @classproperty
        def default_member_filter(cls):
            return cls.outer_class.Meta.default_authenticated_filter

        @classproperty
        def default_curator_filter(cls):
            return cls.outer_class.Meta.default_request_community_filter()

        @classproperty
        def default_publisher_filter(cls):
            return cls.outer_class.Meta.default_member_filter

        @classproperty
        def default_author_filter(cls):
            return Bool(should=[
                cls.outer_class.Meta.default_member_filter,
                Q('term', access__owned_by=current_user.id)
            ], minimum_should_match=1)

        @staticmethod
        def default_request_community_filter():
            community_id = community_id_from_request()

            return Bool(should=[
                Q('term', **{current_oarepo_communities.primary_community_field: community_id}),
                terms_filter(current_oarepo_communities.communities_field)([community_id])
            ], minimum_should_match=1)

        @staticmethod
        def default_multi_community_filter(community_list):
            return Bool(must=[
                Bool(should=[
                    Q('terms',
                      **{current_oarepo_communities.primary_community_field: community_list}),
                    Q('terms', **{current_oarepo_communities.communities_field: community_list})
                ], minimum_should_match=1)])

        @classmethod
        def default_filter_factory(cls, search=None, **kwargs):
            f"""Default filter factory for Community records search.

                The following filters applies according to current user roles
                and community ID from requested collection path:

                * Anonymous or with no role in community: default_any_filter
                * Members: default_author_filter
                * Curators: default_curator_filter
                * Publishers: default_publisher_filter

                If the community ID could not be determined from request,
                the *default_multi_community_filter* applies instead.
            """
            q = cls.outer_class.Meta.default_any_filter

            if current_user.is_authenticated:
                if not community_id_from_request():
                    # Filter records for all user's communities
                    user_communities = current_user_communities()

                    return Bool(should=[
                        q,
                        Bool(must=[
                            # TODO: implement per-community filters based on roles in each community
                            Q('terms', state=[STATE_APPROVED, STATE_PUBLISHED]),
                            cls.outer_class.Meta.default_multi_community_filter(user_communities)])
                    ], minimum_should_match=1)
                else:
                    # Filter records in request-sourced community
                    if community_member_permission_impl(None).can():
                        q = Bool(should=[
                            q,
                            cls.outer_class.Meta.default_author_filter
                        ], minimum_should_match=1)
                    if community_curator_permission_impl(None).can():
                        q = Bool(should=[
                            q,
                            cls.outer_class.Meta.default_curator_filter
                        ], minimum_should_match=1)
                    if community_publisher_permission_impl(None).can():
                        q = Bool(should=[
                            q,
                            cls.outer_class.Meta.default_publisher_filter
                        ], minimum_should_match=1)
            return q

    @classproperty
    @functools.lru_cache(maxsize=1)
    def Meta(cls):
        return type(f'{cls.__name__}.Meta', (cls.ActualMeta,), {'outer_class': cls})


CommunitySearch = CommunitySearchMixin


def community_search_factory(list_resource, records_search, **kwargs):
    community_id = community_id_from_request()

    endpoint = request.endpoint
    endpoint = endpoint.split('.')[1]
    endpoint = re.sub('_list$', '', endpoint)

    index_name = records_search._index

    kwargs["query_parser"] = functools.partial(query_parser, index_name=index_name,
                                               endpoint_name=endpoint)

    query, params = es_search_factory(list_resource, records_search, **kwargs)
    print(query, params)
    if community_id:
        params = {
            **params,
            'community_id': community_id
        }
    return query, params
