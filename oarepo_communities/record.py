# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from jsonpatch import apply_patch


class CommunityKeepingMixin(object):
    """A mixin that keeps community info in the metadata."""
    PRIMARY_COMMUNITY_FIELD = '_primary_community'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clear(self):
        """Preserves the schema even if the record is cleared and all metadata wiped out."""
        primary = self.get(self.PRIMARY_COMMUNITY_FIELD)
        super().clear()
        if primary:
            self[self.PRIMARY_COMMUNITY_FIELD] = primary

    def _check_community(self, data):
        if self.PRIMARY_COMMUNITY_FIELD in data:
            if data[self.PRIMARY_COMMUNITY_FIELD] != self[self.PRIMARY_COMMUNITY_FIELD]:
                raise AttributeError('_primary_community cannot be changed')

    def update(self, e=None, **f):
        """Dictionary update."""
        self._check_community(e or f)
        return super().update(e, **f)

    def __setitem__(self, key, value):
        """Dict's setitem."""
        if key == self.PRIMARY_COMMUNITY_FIELD:
            if self.PRIMARY_COMMUNITY_FIELD in self and self[self.PRIMARY_COMMUNITY_FIELD] != value:
                raise AttributeError('_primary_community cannot be changed')
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        """Dict's delitem."""
        if key == self.PRIMARY_COMMUNITY_FIELD:
            raise AttributeError('Primary Community can not be deleted')
        return super().__delitem__(key)

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        """
        Creates a new record instance and store it in the database.
        For parameters see :py:class:invenio_records.api.Record
        """
        if not data.get(cls.PRIMARY_COMMUNITY_FIELD, None):
            raise AttributeError('_primary_community is missing from record')
        ret = super().create(data, id_, **kwargs)
        return ret

    def patch(self, patch):
        """Patch record metadata. Overrides invenio patch to check if community has changed
        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        if self[self.PRIMARY_COMMUNITY_FIELD] != data[self.PRIMARY_COMMUNITY_FIELD]:
            raise AttributeError('_primary_community cannot be changed')
        return self.__class__(data, model=self.model)
