# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from collections import namedtuple

from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_rest.errors import PIDDoesNotExistRESTError
from invenio_records_rest.utils import PIDConverter, LazyPIDValue

from oarepo_communities.constants import PRIMARY_COMMUNITY_FIELD, SECONDARY_COMMUNITY_FIELD


community_lazy_pid_value = namedtuple('community_lazy_pid_value', 'data')


class CommunityPIDValue(str):

    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)

    def __init__(self, pid_value, community_id):
        self.community_id = community_id

    def __eq__(self, other):
        if not isinstance(other, CommunityPIDValue):
            return False
        return self.community_id == other.community_id and str(self) == str(other)


class CommunityPIDConverter(PIDConverter):
    """Community records PID converter."""

    regex = "[^/]+/[^/]+"
    weight = 200

    def to_python(self, value):
        """Resolve PID value."""
        community, pid_value = value.split('/')
        lazy_pid = super().to_python(pid_value)
        pid, record = lazy_pid.data

        if community != record[PRIMARY_COMMUNITY_FIELD] and community not in (record[SECONDARY_COMMUNITY_FIELD] or []):
            raise PIDDoesNotExistRESTError(
                pid_error=PIDDoesNotExistError(pid_type=pid.pid_type, pid_value=pid.pid_value))

        pid.pid_value = CommunityPIDValue(pid.pid_value, record[PRIMARY_COMMUNITY_FIELD])
        return lazy_pid

    def to_url(self, value):
        if isinstance(value, LazyPIDValue):
            value = value.data[0].pid_value

        return f'{super().to_url(value.community_id)}/{super().to_url(value)}'
