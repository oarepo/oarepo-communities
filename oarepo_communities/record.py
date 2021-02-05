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
        if self.PRIMARY_COMMUNITY_FIELD not in self:
            self[self.PRIMARY_COMMUNITY_FIELD] = ''  # TODO: what should be set here????
        else:
            self._check_primary_community(self)

    def clear(self):
        """Preserves the schema even if the record is cleared and all metadata wiped out."""
        primary = self.get(self.PRIMARY_COMMUNITY_FIELD)
        super().clear()
        if primary:
            self[self.PRIMARY_COMMUNITY_FIELD] = primary

    def update(self, e=None, **f):
        """Dictionary update."""
        self._check_primary_community(e or f)
        return super().update(e, **f)

    @classmethod
    def _check_primary_community(cls, data):
        # TODO: check if primary community is valid for a record
        return

    def __setitem__(self, key, value):
        """Dict's setitem."""
        if key == self.PRIMARY_COMMUNITY_FIELD:
            self._check_primary_community(value)
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
        if cls.PRIMARY_COMMUNITY_FIELD not in data:
            data[cls.PRIMARY_COMMUNITY_FIELD] = ''  # TODO: what should be set here????
        else:
            cls._check_primary_community(data)
        ret = super().create(data, id_, **kwargs)
        return ret

    def patch(self, patch):
        """Patch record metadata. Overrides invenio patch to check if schema has changed
        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        self._check_primary_community(data)
        return self.__class__(data, model=self.model)
