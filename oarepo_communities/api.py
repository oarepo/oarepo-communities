# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_db import db
from invenio_records.api import RecordBase

from oarepo_communities.models import OARepoCommunityModel


class OARepoCommunity(RecordBase):
    model_cls = OARepoCommunityModel

    @classmethod
    def create(cls, data, members_id, curators_id, publishers_id, id_=None, **kwargs):
        """Create a new Community instance and store it in the database."""
        with db.session.begin_nested():
            comm = cls(data)
            comm.model = cls.model_cls(
                id=id_,
                members_id=members_id,
                curators_id=curators_id,
                publishers_id=publishers_id,
                json=comm)
            db.session.add(comm.model)

        return comm
