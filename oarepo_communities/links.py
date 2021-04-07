# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_pidstore.fetchers import FetchedPID
from invenio_pidstore.models import PersistentIdentifier
from oarepo_fsm.links import record_fsm_links_factory

from oarepo_communities.converters import CommunityPIDValue
from oarepo_communities.proxies import current_oarepo_communities


def community_record_links_factory(pid, record=None, **kwargs):
    """Ensures that primary community is set in self link."""
    if not isinstance(pid.pid_value, CommunityPIDValue):
        if record:
            primary_community = record[current_oarepo_communities.primary_community_field]
        elif 'record_hit' in kwargs:
            primary_community = kwargs['record_hit']['_source'][current_oarepo_communities.primary_community_field]
        else:
            raise AttributeError('Record or record hit is missing')

        if isinstance(pid, FetchedPID):
            pid = FetchedPID(pid.provider, pid.pid_type, CommunityPIDValue(pid.pid_value, primary_community))
        elif isinstance(pid, PersistentIdentifier):
            pid.pid_value = CommunityPIDValue(pid.pid_value, primary_community)
        else:
            raise NotImplementedError

    links = record_fsm_links_factory(pid, record, **kwargs)

    return links
