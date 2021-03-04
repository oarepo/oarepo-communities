# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from jsonpatch import apply_patch
from oarepo_fsm.decorators import transition
from oarepo_fsm.permissions import require_any

from oarepo_communities.constants import COMMUNITY_REQUEST_APPROVAL, PRIMARY_COMMUNITY_FIELD, SECONDARY_COMMUNITY_FIELD
from oarepo_communities.permissions import permission_factory


class CommunityRecordMixin(object):
    """A mixin that keeps community info in the metadata."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def primary_community(self):
        return self[PRIMARY_COMMUNITY_FIELD]

    @property
    def secondary_communities(self) -> list:
        return self.get(SECONDARY_COMMUNITY_FIELD, []) or []

    def clear(self):
        """Preserves the schema even if the record is cleared and all metadata wiped out."""
        primary = self.get(PRIMARY_COMMUNITY_FIELD)
        super().clear()
        if primary:
            self[PRIMARY_COMMUNITY_FIELD] = primary

    def _check_community(self, data):
        if PRIMARY_COMMUNITY_FIELD in data:
            if data[PRIMARY_COMMUNITY_FIELD] != self.primary_community:
                raise AttributeError('Primary Community cannot be changed')

    def update(self, e=None, **f):
        """Dictionary update."""
        self._check_community(e or f)
        return super().update(e, **f)

    def __setitem__(self, key, value):
        """Dict's setitem."""
        if key == PRIMARY_COMMUNITY_FIELD:
            if PRIMARY_COMMUNITY_FIELD in self and self.primary_community != value:
                raise AttributeError('Primary Community cannot be changed')
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        """Dict's delitem."""
        if key == PRIMARY_COMMUNITY_FIELD:
            raise AttributeError('Primary Community can not be deleted')
        return super().__delitem__(key)

    @classmethod
    def create(cls, data=dict, id_=None, **kwargs):
        """
        Creates a new record instance and store it in the database.
        For parameters see :py:class:invenio_records.api.Record
        """
        if not data.get(PRIMARY_COMMUNITY_FIELD, None):
            raise AttributeError('Primary Community is missing from record')

        ret = super().create(data, id_, **kwargs)
        return ret

    def patch(self, patch):
        """Patch record metadata. Overrides invenio patch to check if community has changed
        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        if self.primary_community != data[PRIMARY_COMMUNITY_FIELD]:
            raise AttributeError('Primary Community cannot be changed')
        return self.__class__(data, model=self.model)

    @transition(src=[None, 'filling'], dest='approving',
                permissions=require_any(permission_factory(COMMUNITY_REQUEST_APPROVAL)))
    def request_approval(self, **kwargs):
        pass
