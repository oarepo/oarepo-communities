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

from oarepo_communities.proxies import current_oarepo_communities

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

    def __init__(self, url_map, pid_type, getter=None, record_class=None,
                 object_type='rec', model=None):
        """Initialize a PIDConverter."""
        self.model = model
        super().__init__(url_map, pid_type, getter=getter, record_class=record_class, object_type=object_type)

    @property
    def weight(self):
        return 200 + 100 * len(self.model.split('/')) if self.model else 0

    @property
    def regex(self):
        if self.model:
            return f'[^/]+/{self.model}/[^/]+'
        else:
            return f'[^/]+/[^/]+'

    def to_python(self, value):
        """Resolve PID value."""
        args = value.split('/')
        community, pid_value = args[0], args[-1]
        lazy_pid = super().to_python(pid_value)
        pid, record = lazy_pid.data

        if community != current_oarepo_communities.get_primary_community_field(record) \
            and community not in (current_oarepo_communities.get_communities_field(record) or []):
            raise PIDDoesNotExistRESTError(
                pid_error=PIDDoesNotExistError(pid_type=pid.pid_type, pid_value=pid.pid_value))

        pid.pid_value = CommunityPIDValue(pid.pid_value, current_oarepo_communities.get_primary_community_field(record))
        return lazy_pid

    def to_url(self, value):
        if isinstance(value, LazyPIDValue):
            value = value.data[0].pid_value

        return f'{super().to_url(value.community_id)}/{f"{self.model}/" if self.model else ""}{super().to_url(value)}'
