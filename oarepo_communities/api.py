# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import current_app
from invenio_db import db
from invenio_records.api import RecordBase
from sqlalchemy import or_

from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.signals import before_community_insert, after_community_insert


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

            before_community_insert.send(
                current_app._get_current_object(),
                community=comm.model
            )
            db.session.add(comm.model)

        after_community_insert.send(
            current_app._get_current_object(),
            community=comm.model
        )

        return comm.model

    @classmethod
    def get_community(cls, id_, with_deleted=False):
        """Retrieve the community by its id.

        Raise a database exception if the community does not exist.

        :param id_: community ID.
        :param with_deleted: If `True` then it includes deleted communities.
        :returns: The :class:`OARepoCommunityModel` instance.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(cls.model_cls.json != None)  # noqa
            obj = query.one()
            return cls(obj.json, model=obj).model

    @classmethod
    def get_community_from_role(cls, role):
        """Retrieve the community for a given role.

        :param role: A flask Role instance
        :returns: The :class:`OARepoCommunityModel` instance,
                  None if role is not associated with any community.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter(or_(cls.model_cls.members_id == role.id,
                                                   cls.model_cls.curators_id == role.id,
                                                   cls.model_cls.publishers_id == role.id))
            obj = query.one_or_none()
            if obj:
                return cls(obj.json, model=obj).model

    @classmethod
    def get_communities(cls, ids, with_deleted=False):
        """Retrieve multiple communities by id.

        :param ids: List of community IDs.
        :param with_deleted: If `True` then it includes deleted communities.
        :returns: A list of :class:`OARepoCommunityModel` instances.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter(cls.model_cls.id.in_(ids))
            if not with_deleted:
                query = query.filter(cls.model_cls.json != None)  # noqa

            return [cls(obj.json, model=obj).model for obj in query.all()]
