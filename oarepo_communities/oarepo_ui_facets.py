# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from oarepo_communities.api import OARepoCommunity


def filter_facet_options(sender, index_name, index, view_kwargs, **kwargs):
    community_id = view_kwargs.get('community_id', None)
    if community_id:
        community = OARepoCommunity.get_community(community_id)
        excluded_facets = community.excluded_facets.get(index_name, None)
        if not excluded_facets:
            return

        index['aggs'] = {k: v for k, v in index['aggs'].items() if k in excluded_facets}
        index['filters'] = {k: v for k, v in index['filters'].items() if k in excluded_facets}


try:
    from oarepo_ui.signals import before_facet_options

    before_facet_options.connect(filter_facet_options)
except ImportError:
    pass
