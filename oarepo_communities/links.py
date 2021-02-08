# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import url_for
from invenio_records_rest import current_records_rest
from invenio_records_rest.links import default_links_factory


def record_collection_links_factory(pid, record=None, **kwargs):
    """Ensures that primary collection is set in self link."""
    links = default_links_factory(pid, record, **kwargs)
    endpoint = '.{0}_item'.format(
        current_records_rest.default_endpoint_prefixes[pid.pid_type])
    primary_community = None

    if record:
        primary_community = record['_primary_community']
    elif 'record_hit' in kwargs:
        primary_community = kwargs['record_hit']['_source']['_primary_community']

    if primary_community:
        links['self'] = url_for(endpoint,
                                pid_value=pid.pid_value,
                                _external=True,
                                community_id=primary_community)
    return links
